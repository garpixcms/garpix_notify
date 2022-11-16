import json
import os
import re
from datetime import datetime
from typing import Optional, List

import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models, transaction
from django.db.models import Manager
from django.utils.html import format_html
from django.utils.module_loading import import_string
from django.db.models.signals import post_save
from django.dispatch import receiver

from .log import NotifyErrorLog
from .user_list import NotifyUserList
from .category import NotifyCategory
from .choices import TYPE, STATE, StatusMessage
from .file import NotifyFile
from .template import NotifyTemplate
from ..exceptions import IsInstanceException
from ..mixins import UserNotifyMixin
from ..utils.send_data import SendData

from ..clients import SMSClient, EmailClient, CallClient, TelegramClient, ViberClient, PushClient, WhatsAppClient

NotifyMixin = import_string(getattr(settings, 'GARPIX_NOTIFY_MIXIN', 'garpix_notify.mixins.notify_mixin.NotifyMixin'))

User = get_user_model()


class Notify(NotifyMixin, UserNotifyMixin):
    """
    Уведомление
    """
    subject = models.CharField(max_length=255, default='', blank=True, verbose_name='Тема')
    text = models.TextField(verbose_name='Текст')
    html = models.TextField(verbose_name='HTML', blank=True, default='')

    user: User = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True, on_delete=models.SET_NULL,
                                   related_name='notifies', verbose_name='Пользователь (получатель)')
    email = models.EmailField(max_length=255, blank=True, null=True, verbose_name='Email Получателя',
                              help_text='Используется только в случае отсутствия указанного пользователя')
    sender_email = models.EmailField(max_length=255, blank=True, null=True, verbose_name='Email Отправителя')

    state = models.IntegerField('Состояние', choices=STATE.CHOICES, default=STATE.WAIT)
    event = models.IntegerField('Событие', choices=settings.CHOICES_NOTIFY_EVENT, blank=True, null=True)
    room_name = models.CharField('Название комнаты', max_length=255, null=True, blank=True)
    type = models.IntegerField(choices=TYPE.CHOICES, verbose_name='Тип')
    category = models.ForeignKey(NotifyCategory, on_delete=models.CASCADE, related_name='notifies',
                                 verbose_name='Категория')

    files = models.ManyToManyField(NotifyFile, verbose_name='Файлы')

    is_read = models.BooleanField(default=False, verbose_name='Прочитано')
    data_json = models.TextField(blank=True, null=True, verbose_name='Данные пуш-уведомления (JSON)')

    users_list = models.ManyToManyField(NotifyUserList, blank=True, verbose_name='Списки пользователей для рассылки')

    send_at = models.DateTimeField(blank=True, null=True, verbose_name='Время начала отправки')
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    sent_at = models.DateTimeField('Дата отправки', blank=True, null=True)

    is_delete_after = models.BooleanField(default=False, verbose_name='Удалять после отправки')

    objects = Manager()

    def __str__(self):
        return self.subject if self.subject and self.subject != '' else f'Уведомление № {self.id}'

    def _get_sender(self):
        if self.user:
            self.email = self.user.email if self.user.email else self.email
            self.phone = str(self.user.phone) if self.user.phone else str(self.phone)
            self.telegram_chat_id = self.user.telegram_chat_id if self.user.telegram_chat_id else self.telegram_chat_id
            self.viber_chat_id = self.user.viber_chat_id if self.user.viber_chat_id else self.viber_chat_id

        if self.phone is not None:
            self.phone = re.sub(r"\D", "", self.phone)

    def start_send(self):  # noqa

        # Если передан пользователь, то перезаписываем данные (если они есть у пользователя)
        self._get_sender()

        if self.type == TYPE.EMAIL:
            EmailClient.send_email(self)
        elif self.type == TYPE.SMS:
            SMSClient.send_sms(self)
        elif self.type == TYPE.PUSH:
            PushClient.send_push(self)
        elif self.type == TYPE.TELEGRAM:
            TelegramClient.send_telegram(self)
        elif self.type == TYPE.VIBER:
            ViberClient.send_viber(self)
        elif self.type == TYPE.CALL:
            CallClient.send_call(self)
        elif self.type == TYPE.WHATSAPP:
            WhatsAppClient.send_whatsapp(self)

        if self.is_delete_after and self.state == STATE.DELIVERED:
            self._delete_notify()
        else:
            self.save()

    @staticmethod
    def send(event: int, context: dict, user: User = None, email: str = None, phone: str = None,  # noqa: C901
             files: list = None, data_json: dict = None, viber_chat_id: str = None, room_name: str = None,
             notify_templates: list = None, send_at: datetime = None, send_now: bool = False,
             user_want_message_check: bool = False, **kwargs) -> List[Optional['Notify']]:

        if user and not isinstance(user, User):
            raise IsInstanceException()

        instance_list: list = []

        # Сначала забираем те данные, которые передали с методом
        notify_user = user if user else None
        notify_email = email if email else None
        notify_phone = phone if phone else None
        notify_viber_chat_id = viber_chat_id if viber_chat_id else None

        local_context = context.copy()
        data_json = json.dumps(data_json) if data_json else None

        if notify_templates:
            templates = (
                NotifyTemplate.objects
                .select_related('category', 'user')
                .prefetch_related('user_lists')
                .filter(id__in=notify_templates, event=event, is_active=True)
            )
        else:
            templates = (
                NotifyTemplate.objects
                .select_related('category', 'user')
                .prefetch_related('user_lists')
                .filter(event=event, is_active=True)
            )

        file_instances = []
        if files:
            file_instances = list(map(lambda file: NotifyFile.objects.create(file=file), files))

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
                notify_viber_chat_id = (
                    notify_user.viber_chat_id if notify_user.viber_chat_id else notify_viber_chat_id
                )

            if notify_user is None and template_user:
                notify_user = template.user if template.user else None
                notify_email = template.user.email if template.user.email else notify_email
                notify_phone = template.user.phone if template.user.phone else notify_phone
                notify_viber_chat_id = (
                    template.user.viber_chat_id if template.user.viber_chat_id else notify_viber_chat_id
                )

            if notify_email is None:
                notify_email = template_email

            if notify_phone is None:
                notify_phone = template_phone

            if notify_viber_chat_id is None:
                notify_viber_chat_id = template_viber_chat_id

            # Проверка, хочет ли пользователь получить сообщение
            if user_want_message_check and hasattr(
                    settings, 'NOTIFY_USER_WANT_MESSAGE_CHECK') and settings.NOTIFY_USER_WANT_MESSAGE_CHECK is not None:

                user_want_message = import_string(settings.NOTIFY_USER_WANT_MESSAGE_CHECK)

                if not notify_users_lists.exists():
                    user_check = user_want_message(event, template.type, notify_user)
                    if not user_check:
                        continue
                else:
                    # Если у нас шаблон со списками, то формируем новый из переданных пользователей,
                    # Если список пустой, то отменяем отправку
                    notify_users_lists = user_want_message(event, template.type, notify_user, notify_users_lists)
                    if not notify_users_lists:
                        continue

            # Передаем пользователя в контекст
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

            if send_at is not None:
                notify_send = send_at
            else:
                notify_send = template.send_at

            instance = Notify.objects.create(
                subject=template.render_subject(local_context),
                text=template.render_text(local_context),
                html=template.render_html(local_context),
                user=notify_user,
                email=notify_email,
                phone=notify_phone if notify_phone is not None else "",
                viber_chat_id=notify_viber_chat_id if notify_viber_chat_id is not None else "",
                type=template.type,
                event=template.event,
                category=template.category if template.category else None,
                data_json=data_json,
                send_at=notify_send,
                room_name=room_name,
                is_delete_after=template.is_delete_after,
                **kwargs
            )
            if notify_users_lists.exists():
                instance.users_list.add(*notify_users_lists)
            file_instance = instance.files
            for f in file_instances:
                file_instance.add(f)
            instance.save()

            if send_now:
                transaction.on_commit(lambda: instance.start_send())

            instance_list.append(instance)
        return instance_list

    @staticmethod
    def call(phone: str, user: User = None, url: str = None, **kwargs) -> Optional[str]:
        call_url_type: int = CallClient.get_url_type()

        if user and not isinstance(user, User):
            raise IsInstanceException()

        if user is not None:
            phone = user.phone if user.phone else phone

        if url is not None:
            url = url
        else:
            url = SendData.call_url(call_url_type)

        main_url = url.format(to=phone, **kwargs)
        response_url = requests.get(main_url)
        response_dict: dict = response_url.json()
        value, response = CallClient.get_value_checker(response_dict)

        if value == "OK":
            return '{Code}'.format(**response)
        return None

    def to_log(self, error_text: str) -> None:
        log: NotifyErrorLog = NotifyErrorLog(notify=self, error=error_text)
        log.save()

    def get_format_state(self):
        undefined = '<span style="color:black;">Неизвестный статус</span>'
        status: str = StatusMessage.STATUS.get(self.state, undefined)
        return format_html(status)

    get_format_state.short_description = 'Статус'

    def _delete_notify(self) -> None:
        files = self.files.all()
        if files.exists():
            for file in files:
                file_path = f'{settings.MEDIA_ROOT}/{file.file}'
                if os.path.isfile(file_path):
                    os.remove(file_path)
            files.delete()
        self.delete()

    class Meta:
        verbose_name = 'Уведомление'
        verbose_name_plural = 'Уведомления'


@receiver(post_save, sender=Notify)
def system_post_save(sender, instance, created, **kwargs):
    from garpix_notify.tasks.tasks import send_system_notifications
    if created and instance.type == TYPE.SYSTEM:
        transaction.on_commit(lambda: send_system_notifications.delay(instance.pk))
