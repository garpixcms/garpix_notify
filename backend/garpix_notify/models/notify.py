import json
import re
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from typing import Optional
from smtplib import SMTP, SMTP_SSL
from django.conf import settings
from django.db import models, transaction
from django.db.models import Q
from django.template import Template, Context
from django.utils.html import format_html
from django.utils.module_loading import import_string
from django.utils.safestring import mark_safe
from django.utils.timezone import now
from django.db.models.signals import post_save
from django.dispatch import receiver
from viberbot import Api, BotConfiguration
from viberbot.api.messages import TextMessage

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
from ..utils import receiving_users
from ..utils.sms_checker import SMSClient
from ..utils.call_code_cheker import CallClient
from ..utils.send_data import notify_create


def chunks(s, n):
    """Produce `n`-character chunks from `s`."""
    for start in range(0, len(s), n):
        yield s[start:start + n]


try:
    config = NotifyConfig.get_solo()
    IS_PUSH_ENABLED = config.is_push_enabled
    IS_TELEGRAM_ENABLED = config.is_telegram_enabled
    TELEGRAM_API_KEY = config.telegram_api_key
    IS_VIBER_ENABLED = config.is_viber_enabled
    VIBER_API_KEY = config.viber_api_key
    VIBER_BOT_NAME = config.viber_bot_name
    IS_EMAIL_ENABLED = config.is_email_enabled
    EMAIL_MALLING = config.email_malling
    TELEGRAM_PARSE_MODE = config.telegram_parse_mode
    TELEGRAM_DISABLE_NOTIFICATION = config.telegram_disable_notification
    TELEGRAM_DISABLE_PAGE_PREVIEW = config.telegram_disable_web_page_preview
    TELEGRAM_SENDING_WITHOUT_REPLY = config.telegram_allow_sending_without_reply
    TELEGRAM_TIMEOUT = config.telegram_timeout
except Exception:
    IS_PUSH_ENABLED = True
    IS_TELEGRAM_ENABLED = True
    IS_VIBER_ENABLED = True
    IS_EMAIL_ENABLED = True
    TELEGRAM_PARSE_MODE = getattr(settings, 'TELEGRAM_PARSE_MODE', None)
    TELEGRAM_DISABLE_NOTIFICATION = getattr(settings, 'TELEGRAM_DISABLE_NOTIFICATION', False)
    TELEGRAM_DISABLE_PAGE_PREVIEW = getattr(settings, 'TELEGRAM_DISABLE_PAGE_PREVIEW', False)
    TELEGRAM_SENDING_WITHOUT_REPLY = getattr(settings, 'TELEGRAM_SENDING_WITHOUT_REPLY', False)
    TELEGRAM_TIMEOUT = getattr(settings, 'TELEGRAM_TIMEOUT', None)
    TELEGRAM_API_KEY = getattr(settings, 'TELEGRAM_API_KEY', '000000000:AAAAAAAAAA-AAAAAAAA-_AAAAAAAAAAAAAA')
    VIBER_API_KEY = getattr(settings, 'VIBER_API_KEY', '000000000:AAAAAAAAAA-AAAAAAAA-_AAAAAAAAAAAAAA')
    VIBER_BOT_NAME = getattr(settings, 'VIBER_BOT_NAME', 'MySuperBot')
    EMAIL_MALLING = getattr(settings, 'EMAIL_MALLING', 1)

NotifyMixin = import_string(settings.GARPIX_NOTIFY_MIXIN)


class Notify(NotifyMixin, UserNotifyMixin, SMSClient, CallClient):
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
                                 verbose_name='Категория')
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
        if self.type == TYPE.CALL:
            self.send_call_code()

        self.save()

    def send_email(self):
        account = self._get_valid_smtp_account()
        emails = []
        if self.users_list.all().count() != 0:
            users_list = self.users_list.all()
            emails = (receiving_users(users_list, value='email'))
            if self.email:
                emails.append(self.email)
        else:
            emails.append(self.email)

        try:
            body = self._render_body(mail_from=account.sender, layout=self.category, emails=emails)
            server = SMTP_SSL(account.host, account.port) if account.is_use_ssl else SMTP(account.host, account.port)
            server.ehlo()
            if account.is_use_tls:
                server.starttls()
            server.login(account.username, account.password)
            server.sendmail(account.sender, emails, body.as_string())
            server.close()
            self.state = STATE.DELIVERED
            self.sent_at = now()
        except Exception as e:  # noqa
            self.state = STATE.REJECTED
            self.to_log(str(e))

    def send_push(self):

        if not IS_PUSH_ENABLED:
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
        bot = telegram.Bot(token=TELEGRAM_API_KEY)
        parse_mode = TELEGRAM_PARSE_MODE if TELEGRAM_PARSE_MODE != '' else None
        if not IS_TELEGRAM_ENABLED:
            self.state = STATE.DISABLED
            return

        try:
            result = False
            for chunk in chunks(str(self.text), 4096):
                result = bot.sendMessage(chat_id=self.telegram_chat_id,
                                         text=chunk,
                                         parse_mode=parse_mode,
                                         disable_web_page_preview=TELEGRAM_DISABLE_PAGE_PREVIEW,
                                         disable_notification=TELEGRAM_DISABLE_NOTIFICATION,
                                         timeout=TELEGRAM_TIMEOUT,
                                         allow_sending_without_reply=TELEGRAM_SENDING_WITHOUT_REPLY)
            if result:
                self.state = STATE.DELIVERED
                self.sent_at = now()
            else:
                self.state = STATE.REJECTED
                self.to_log('REJECTED WITH DATA, please test it.')
        except Exception as e:  # noqa
            self.state = STATE.REJECTED
            self.to_log(str(e))

    def _render_body(self, mail_from, layout, emails):
        msg = MIMEMultipart('alternative')
        if len(emails) > 1:
            if EMAIL_MALLING == 1:
                msg['BCC'] = ', '.join(emails)
            else:
                msg['СС'] = ', '.join(emails)
        else:
            msg['To'] = ''.join(emails)
        msg['Subject'] = Header(self.subject, 'utf-8')
        msg['From'] = mail_from

        text = MIMEText(self.text, 'plain', 'utf-8')
        msg.attach(text)

        if self.html:
            template = Template(layout.template)
            context = Context({'text': mark_safe(self.html)})
            html = MIMEText(mark_safe(template.render(context)), 'html', 'utf-8')
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
        viber = Api(BotConfiguration(
            name=VIBER_BOT_NAME,
            avatar='',
            auth_token=VIBER_API_KEY
        ))
        if not IS_VIBER_ENABLED:
            self.state = STATE.DISABLED
            return
        try:
            result = False
            if self.users_list.all().exists():
                participants = receiving_users(self.users_list.all(), value='viber_chat_id')
                if participants:
                    for participant in participants:
                        result = viber.send_messages(to=participant, messages=[TextMessage(text=self.text)])
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
        if not IS_EMAIL_ENABLED:
            self.state = STATE.DISABLED
            return

        account = SMTPAccount.get_free_smtp()
        self.sender_email = account.sender
        if account is None or not account.is_active:
            return

        return account

    @staticmethod
    def send(event, context, user=None, email=None, phone=None, files=None, data_json=None,  # noqa
             viber_chat_id=None, room_name=None, notify_templates=None, send_at=None, **kwargs):

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

        # Для выбора шаблонов из Категории или по ивенту
        if notify_templates:
            templates = NotifyTemplate.objects.filter(id__in=notify_templates, event=event, is_active=True)
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

    class Meta:
        verbose_name = 'Уведомление'
        verbose_name_plural = 'Уведомления'


@receiver(post_save, sender=Notify)
def system_post_save(sender, instance, created, **kwargs):
    from garpix_notify.tasks.tasks import send_system_notifications
    if created and instance.type == TYPE.SYSTEM:
        transaction.on_commit(lambda: send_system_notifications.delay(instance.pk))
