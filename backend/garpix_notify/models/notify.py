import json
import re
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional
from smtplib import SMTP, SMTP_SSL
import requests
from django.conf import settings
from django.db import models, transaction
from django.db.models import Q
from django.template import Template, Context
from django.utils.html import format_html
from django.utils.module_loading import import_string
from django.utils.safestring import mark_safe
from django.utils.timezone import now
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from viberbot import Api, BotConfiguration
from viberbot.api.messages import TextMessage

from user.models import User
from .user_list import NotifyUserList
from .category import NotifyCategory
from .choices import TYPE, STATE
from .config import NotifyConfig
from .fcm import NotifyDevice
from .file import NotifyFile
from .log import NotifyErrorLog
from .smtp import SMTPAccount
from .template import NotifyTemplate
from ..mixins import UserNotifyMixin
from ..utils import sms_checker, receiving


def chunks(s, n):
    """Produce `n`-character chunks from `s`."""
    for start in range(0, len(s), n):
        yield s[start:start + n]


class Notify(UserNotifyMixin):
    """
    Уведомление
    """

    # title = models.CharField(max_length=255, verbose_name='Название для админа')
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

    def _send(self):
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
            self.send_email()
        if self.type == TYPE.SMS:
            self.send_sms()
        if self.type == TYPE.PUSH:
            self.send_push()
        if self.type == TYPE.TELEGRAM:
            self.send_telegram()
        if self.type == TYPE.VIBER:
            self.send_viber()

        self.save()

    def send_email(self):
        account = self._get_valid_smtp_account()

        try:
            body = self._render_body(account.sender, self.category)
            server = SMTP_SSL(account.host, account.port) if account.is_use_ssl else SMTP(account.host, account.port)
            server.ehlo()
            if account.is_use_tls:
                server.starttls()
            server.login(account.username, account.password)
            server.sendmail(account.sender, [self.email], body.as_string())
            server.close()
            self.state = STATE.DELIVERED
            self.sent_at = now()
        except Exception as e:  # noqa
            self.state = STATE.REJECTED
            self.to_log(str(e))

    def send_sms(self):
        config = NotifyConfig.get_solo()

        if not config.is_sms_enabled:
            self.state = STATE.DISABLED
            return

        try:
            if self.users_list is not None:
                users_list = self.users_list.all()
                receivers = receiving(users_list)
                # Убираем дубликаты пользователей
                receivers = list({v['phone']: v for v in receivers}.values())
                phones = []
                for user in receivers:
                    if user['phone']:
                        phones.append(user['phone'])
                print(phones)
                phones = ', '.join(phones)
            else:
                phones = self.phone
            msg = str(self.text.replace(' ', '+'))
            url = sms_checker(msg, phones, config, NotifyConfig)
            response = requests.get(url)
            try:
                int(response.text)
                self.state = STATE.DELIVERED
                self.sent_at = now()
            except Exception:
                self.state = STATE.REJECTED


        except Exception as e:  # noqa
            self.state = STATE.REJECTED
            self.to_log(str(e))

    def send_push(self):
        config = NotifyConfig.get_solo()

        if not config.is_push_enabled:
            self.state = STATE.DISABLED
            return

        if self.user is None:
            self.state = STATE.REJECTED
            self.save()
            return

        devices = NotifyDevice.objects.filter(active=True, user=self.user).distinct('device_id')

        data_json = {}
        if self.data_json is not None:
            data_json = json.loads(self.data_json)
        data_json.update({
            'notify_id': self.id,
        })

        try:
            devices.send_message(title=self.subject, body=self.text, data=data_json)
            self.state = STATE.DELIVERED
            self.sent_at = now()
        except Exception as e:  # noqa
            self.state = STATE.REJECTED
            self.to_log(str(e))

    def send_telegram(self):
        import telegram
        config = NotifyConfig.get_solo()
        bot = telegram.Bot(token=config.telegram_api_key)

        if not config.is_telegram_enabled:
            self.state = STATE.DISABLED
            return

        try:
            result = False
            for chunk in chunks(str(self.text), 4096):
                result = bot.sendMessage(chat_id=self.telegram_chat_id, text=chunk, disable_web_page_preview=True)
            if result:
                self.state = STATE.DELIVERED
                self.sent_at = now()
            else:
                self.state = STATE.REJECTED
                self.to_log('REJECTED WITH DATA, please test it.')
        except Exception as e:  # noqa
            self.state = STATE.REJECTED
            self.to_log(str(e))

    # todo - упростить метод (too complex)
    @staticmethod
    def send(event, context, category=None, user=None, email=None, phone=None, files=None, data_json=None,  # noqa
             viber_chat_id=None, room_name=None):
        local_context = context.copy()

        if user is not None:
            email = user.email if not email else email
            phone = user.phone if not phone else phone

        user_want_message_check = None
        if hasattr(settings, 'NOTIFY_USER_WANT_MESSAGE_CHECK') and settings.NOTIFY_USER_WANT_MESSAGE_CHECK is not None:
            user_want_message_check = import_string(settings.NOTIFY_USER_WANT_MESSAGE_CHECK)

        # Для выбора шаблонов из Категории или по ивенту
        if category:
            category = NotifyCategory.objects.filter(Q(title=category)).first()
            category_template = category.template_choice.pk
            if category_template:
                templates = NotifyTemplate.objects.filter(
                    Q(pk=category_template) & Q(is_active=True)
                )
        else:
            templates = NotifyTemplate.objects.filter(
                Q(event=event) & Q(is_active=True)
            )
        if files is None:
            files = []

        data_json = json.dumps(data_json) if data_json is not None else None

        file_instances = []
        for f in files:
            instance = NotifyFile.objects.create(file=f)
            file_instances.append(instance)

        notification_count = 0
        recievers = []
        for template in templates:
            # Проверка на наличие списка в шаблоне
            # Если в шаблоне передаются списки пользователей, то отдаем их уведомлениям
            # Если уведомление для одного пользователя, то создаем для одного
            users_lists = template.user_lists.all()

            if users_lists:
                local_context['event_id'] = event
                instance = Notify.objects.create(
                    subject=template.render_subject(local_context),
                    text=template.render_text(local_context),
                    html=template.render_html(local_context),
                    type=template.type,
                    event=template.event,
                    category=category,
                    data_json=data_json,
                    send_at=template.send_at,
                    room_name=room_name,
                )
                instance.users_list.add(*users_lists)
                file_instance = instance.files
                for f in file_instances:
                    file_instance.add(f)
                instance.save()
                notification_count += 1
            else:
                # Формируем список основных и дополнительных получателей письма
                # Первого получателя заполняем из шаблона, его данные могут быть пустыми - чтобы можно было через
                # код отправить уведомление
                if user or phone or email or viber_chat_id:
                    recievers = [{
                        'user': user,
                        'email': email,
                        'phone': phone,
                        'viber_chat_id': viber_chat_id,
                    }]
                for reciever in recievers:
                    template_user = reciever['user']
                    template_email = reciever['email']
                    template_phone = reciever['phone']
                    template_viber_chat_id = reciever['viber_chat_id']
                    # Если в шаблоне не указаны получатели, то получатель тот, кого передали в коде
                    if template_user is None and template_email is None:
                        template_user = user
                        template_email = email
                        template_phone = phone
                        template_viber_chat_id = viber_chat_id
                        # Если пользователь заполнен, то перезаписываем поля емейла и номера телефона,
                        # даже если они были переданы.
                        if user is not None:
                            template_email = user.email
                            template_phone = user.phone
                            template_viber_chat_id = user.viber_chat_id
                    # Проверка, хочет ли получить сообщение
                    if user_want_message_check is not None and not \
                            user_want_message_check(event, template.type, template_user):  # noqa
                        continue

                    # Добавляем пользователя в контекст, если его там не передали
                    if template_user is not None:
                        if local_context is not None:
                            local_context.update({
                                'user': template_user,
                            })
                        else:
                            local_context = {
                                'user': template_user,
                            }
                    local_context['event_id'] = event

                    instance = Notify.objects.create(
                        subject=template.render_subject(local_context),
                        text=template.render_text(local_context),
                        html=template.render_html(local_context),
                        user=template_user,
                        email=template_email,
                        phone=template_phone if template_phone is not None else "",
                        viber_chat_id=template_viber_chat_id if template_viber_chat_id is not None else "",
                        type=template.type,
                        event=template.event,
                        category=category,
                        data_json=data_json,
                        send_at=template.send_at,
                        room_name=room_name
                    )
                    file_instance = instance.files
                    for f in file_instances:
                        file_instance.add(f)
                    instance.save()
                    notification_count += 1

        return notification_count

    def _render_body(self, mail_from, layout):
        msg = MIMEMultipart('alternative')
        if self.users_list is not None:
            users_list = self.users_list.all()
            receivers = receiving(users_list)
            # Убираем дубликаты пользователей
            receivers = list({v['email']: v for v in receivers}.values())
            emails = []
            for user in receivers:
                if user['email']:
                    emails.append(user['email'])
            msg['To'] = ', '.join(emails)
        else:
            msg['To'] = self.email
        msg['Subject'] = self.subject
        msg['From'] = mail_from

        text = MIMEText(self.text, 'plain')
        msg.attach(text)

        if self.html:
            template = Template(layout)
            context = Context({'text': mark_safe(self.html)})
            html = MIMEText(mark_safe(template.render(context)), 'html')
            msg.attach(html)

        for fl in self.files.all():
            with fl.file.open(mode='rb') as f:
                part = MIMEApplication(
                    f.read(),
                    Name=fl.file.name.split('/')[-1]
                )

            part['Content-Disposition'] = 'attachment; filename="%s"' % fl.file.name.split('/')[-1]

            msg.attach(part)

        return msg

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

    def send_viber(self):
        config = NotifyConfig.get_solo()
        viber = Api(BotConfiguration(
            name=config.viber_bot_name,
            avatar='',
            auth_token=config.viber_api_key
        ))
        if not config.is_viber_enabled:
            self.state = STATE.DISABLED
            return
        try:
            result = False
            # из шаблона получаем выбраные списки пользователей для рассылки
            for user_lists_in_template in NotifyTemplate.objects.all().prefetch_related('user_lists'):
                # проверяем добавлены ли списки пользователей для рассылки в шаблон
                if user_lists_in_template.user_lists.all().exists():
                    # перебираем списки пользователей для рассылки
                    for participants_in_user_lists in user_lists_in_template.user_lists.all():
                        # перебираем участников списка пользователей
                        for participant in participants_in_user_lists.participants.all():
                            result = viber.send_messages(to=participant.user.viber_chat_id,
                                                         messages=[TextMessage(text=self.text)])
                # если не добавлены, сообщение приходит пользователю(получателю) или тому, кто указан в коде
                else:
                    result = viber.send_messages(to=self.viber_chat_id, messages=[TextMessage(text=self.text)])
            if result:
                self.state = STATE.DELIVERED
                self.sent_at = now()
            else:
                self.state = STATE.REJECTED
                self.to_log('REJECTED WITH DATA, please test it.')
        except Exception as e:  # noqa
            self.state = STATE.REJECTED
            self.to_log(str(e))

    def _get_valid_smtp_account(self) -> Optional[SMTPAccount]:
        config = NotifyConfig.get_solo()
        if not config.is_email_enabled:
            self.state = STATE.DISABLED
            return

        account = SMTPAccount.get_free_smtp()
        self.sender_email = account.sender
        if account is None or not account.is_active:
            return

        return account

    class Meta:
        verbose_name = 'Уведомление'
        verbose_name_plural = 'Уведомления'


@receiver(post_save, sender=Notify)
def system_post_save(sender, instance, created, **kwargs):
    from garpix_notify.tasks.tasks import send_system_notifications
    if created and instance.type == TYPE.SYSTEM:
        transaction.on_commit(lambda: send_system_notifications.delay(instance.pk))
