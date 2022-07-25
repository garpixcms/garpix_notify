import json
import re

import requests
from django.conf import settings
from django.db import models, transaction
from django.utils.html import format_html
from django.utils.module_loading import import_string
from django.db.models.signals import post_save
from django.dispatch import receiver

from .user_list import NotifyUserList
from .category import NotifyCategory
from .choices import TYPE, STATE
from .file import NotifyFile
from .log import NotifyErrorLog
from .template import NotifyTemplate
from ..mixins import UserNotifyMixin
from ..utils.send_data import url_dict_call, operator_call, response_check, notify_create, system_notify_create
from ..clients import SMSClient, EmailClient, CallClient, TelegramClient, ViberClient, PushClient, WhatsAppClient

NotifyMixin = import_string(settings.GARPIX_NOTIFY_MIXIN)


class Notify(NotifyMixin, UserNotifyMixin):
    """
    Уведомление
    """
    subject = models.CharField(max_length=255, default='', blank=True, verbose_name='Тема')
    text = models.TextField(verbose_name='Текст')
    html = models.TextField(verbose_name='HTML', blank=True, default='')

    user = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True, on_delete=models.SET_NULL,
                             related_name='notifies', verbose_name='Пользователь (получатель)')
    email = models.EmailField(max_length=255, blank=True, null=True, verbose_name='Email Получателя',
                              help_text='Используется только в случае отсутствия указанного пользователя')
    sender_email = models.EmailField(max_length=255, blank=True, null=True, verbose_name='Email Отправителя')

    type = models.IntegerField(choices=TYPE.CHOICES, verbose_name='Тип')
    state = models.IntegerField(choices=STATE.CHOICES, default=STATE.WAIT, verbose_name='Состояние')
    category = models.ForeignKey(NotifyCategory, on_delete=models.CASCADE, related_name='notifies',
                                 verbose_name='Категория', blank=True, null=True)
    event = models.IntegerField(choices=settings.CHOICES_NOTIFY_EVENT, blank=True, null=True, verbose_name='Событие')
    files = models.ManyToManyField(NotifyFile, verbose_name='Файлы')

    is_read = models.BooleanField(default=False, verbose_name='Прочитано')
    data_json = models.TextField(blank=True, null=True, verbose_name='Данные пуш-уведомления (JSON)')
    room_name = models.CharField(max_length=255, null=True, blank=True, verbose_name='Название комнаты')

    users_list = models.ManyToManyField(NotifyUserList, blank=True, verbose_name='Списки пользователей для рассылки')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    send_at = models.DateTimeField(blank=True, null=True, verbose_name='Время начала отправки')
    sent_at = models.DateTimeField(blank=True, null=True, verbose_name='Дата отправки')

    def __str__(self):
        return self.subject

    def get_sender(self):
        pass

    def _send(self):  # noqa
        if self.user:
            self.email = self.user.email
            self.phone = str(self.user.phone)
            self.telegram_chat_id = self.user.telegram_chat_id
            self.viber_chat_id = self.user.viber_chat_id
        elif self.email:
            self.email = self.email

        if self.phone is not None:
            self.phone = re.sub("[^0-9]", "", self.phone)

        if self.type == TYPE.EMAIL:
            EmailClient.send_email(self)
        if self.type == TYPE.SMS:
            SMSClient.send_sms(self)
        if self.type == TYPE.PUSH:
            PushClient.send_push(self)
        if self.type == TYPE.TELEGRAM:
            TelegramClient.send_telegram(self)
        if self.type == TYPE.VIBER:
            ViberClient.send_viber(self)
        if self.type == TYPE.CALL:
            CallClient.send_call(self)
        if self.type == TYPE.WHATSAPP:
            WhatsAppClient.send_whatsapp(self)

        self.save()

    def get_format_state(self):
        if self.state == STATE.WAIT:
            return format_html('<span style="color:orange;">В ожидании</span>')
        elif self.state == STATE.DELIVERED:
            return format_html('<span style="color:green;">Отправлено</span>')
        elif self.state == STATE.REJECTED:
            return format_html('<span style="color:red;">Отклонено</span>')
        elif self.state == STATE.DISABLED:
            return format_html('<span style="color:red;">Отправка запрещена</span>')
        return format_html('<span style="color:black;">Неизвестный статус</span>')

    get_format_state.short_description = 'Статус'

    def to_log(self, error_text):
        log = NotifyErrorLog(notify=self, error=error_text)
        log.save()

    @staticmethod
    def send(event, context, user=None, email=None, phone=None, files=None, data_json=None,  # noqa
             viber_chat_id=None, room_name=None, notify_templates=None, send_at=None, system=False, **kwargs):

        instance = None
        # Сначала забираем те данные, которые передали с методом
        notify_user = user if user else None
        notify_email = email if email else None
        notify_phone = phone if phone else None
        notify_viber_chat_id = viber_chat_id if viber_chat_id else None

        local_context = context.copy()

        user_want_message_check = None
        if hasattr(settings, 'NOTIFY_USER_WANT_MESSAGE_CHECK') and settings.NOTIFY_USER_WANT_MESSAGE_CHECK is not None:
            user_want_message_check = import_string(settings.NOTIFY_USER_WANT_MESSAGE_CHECK)

        data_json = json.dumps(data_json) if data_json is not None else None

        if system:
            if data_json is None:
                data_json = json.dumps(local_context) if local_context is not None else None

            data_dict = system_notify_create(context=data_json, user=notify_user,
                                             email=notify_email, phone=notify_phone, viber=notify_viber_chat_id,
                                             json=data_json, time=send_at, room=room_name, type_notify=TYPE.SYSTEM,
                                             event=event)
            instance = Notify.objects.create(**data_dict, **kwargs)
            return instance

        # Для выбора шаблонов из Категории или по ивенту
        if notify_templates:
            templates = NotifyTemplate.objects.filter(id__in=notify_templates, event=event, is_active=True)
        else:
            templates = NotifyTemplate.objects.filter(event=event, is_active=True)
        if files is None:
            files = []

        file_instances = []
        for f in files:
            instance = NotifyFile.objects.create(file=f)
            file_instances.append(instance)

        for template in templates:

            notify_users_lists = template.user_lists.all()

            # Формируем список основных получателей письма
            # Из шаблона, если методом не было передано данных
            template_user = template.user if template.user else None
            template_email = template.email if template.email else None
            template_phone = template.phone if template.phone else None
            template_viber_chat_id = template.viber_chat_id if template.viber_chat_id else None

            # Данные, которые указал пользователь у себя в профиле в приоритете
            if notify_user:
                notify_email = notify_user.email if notify_user.email else notify_email
                notify_phone = notify_user.phone if notify_user.phone else notify_phone
                notify_viber_chat_id = notify_user.viber_chat_id if notify_user.viber_chat_id else notify_viber_chat_id

            if notify_user is None and template_user:
                notify_user = template.user if template.user else None
                notify_email = template.user.email if template.user.email else notify_email
                notify_phone = template.user.phone if template.user.phone else notify_phone
                notify_viber_chat_id = template.user.viber_chat_id if template.user.viber_chat_id else notify_viber_chat_id

            if notify_email is None:
                notify_email = template_email

            if notify_phone is None:
                notify_phone = template_phone

            if notify_viber_chat_id is None:
                notify_viber_chat_id = template_viber_chat_id

            # Проверка, хочет ли получить сообщение
            if user_want_message_check is not None:  # noqa
                if not notify_users_lists.exists():
                    user_check = user_want_message_check(event, template.type, notify_user)
                    if user_check is None:
                        return None
                else:
                    # Если у нас шаблон со списками, то передаем в функцию и тут формируем новый из тех юзеов,
                    # которым сообщения нужны
                    # Если список пустой, то отменяем отправку
                    notify_users_lists = user_want_message_check(
                        event, template.type, notify_user, notify_users_lists)
                    if notify_users_lists is None:
                        return None
                # Добавляем пользователя в контекст, если его там не передали
            if notify_user is not None:
                if local_context is not None:
                    local_context.update({
                        'user': notify_user,
                    })
                else:
                    local_context = {
                        'user': notify_user,
                    }
            local_context['event_id'] = event

            # Проверка на наличие списка в шаблоне
            # Если в шаблоне передаются списки пользователей, то отдаем их уведомлениям
            # Если уведомление для одного пользователя, то создаем для одного
            # Также идет проверка на время оправки
            if send_at is not None:
                notify_send = send_at
            else:
                notify_send = template.send_at
            data_dict = notify_create(template=template, context=local_context, user=notify_user,
                                      email=notify_email, phone=notify_phone, viber=notify_viber_chat_id,
                                      json=data_json, time=notify_send, room=room_name)
            instance = Notify.objects.create(
                **data_dict,
                **kwargs
            )
            if notify_users_lists.exists():
                instance.users_list.add(*notify_users_lists)
            file_instance = instance.files
            for f in file_instances:
                file_instance.add(f)
            instance.save()

        return instance

    @staticmethod
    def call(phone, user=None, url=None, **kwargs):
        call_url_type = CallClient.CALL_URL_TYPE

        if user is not None:
            phone = user.phone if user.phone else phone
        # Для некоторых операторов из представленного списка, мы можем сгенерировать код на нашей стороне
        # Для этого можем передать в функцию кастомную ссылку и дополнительные параметры
        if url is not None:
            url = url
        else:
            url = url_dict_call[call_url_type]
        main_url = url.format(**operator_call[call_url_type], to=phone, **kwargs)
        response_url = requests.get(main_url)
        response_dict = response_url.json()
        value = CallClient.get_value_checker(response_dict)

        response = response_check(response=response_dict, operator_type=call_url_type, status=value)
        if value == "OK":
            return '{Code}'.format(**response)
        else:
            return None

    class Meta:
        verbose_name = 'Уведомление'
        verbose_name_plural = 'Уведомления'


@receiver(post_save, sender=Notify)
def system_post_save(sender, instance, created, **kwargs):
    from garpix_notify.tasks.tasks import send_system_notifications
    if created and instance.type == TYPE.SYSTEM:
        transaction.on_commit(lambda: send_system_notifications.delay(instance.pk))
