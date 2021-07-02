import re
from typing import Optional

import requests
import json
from django.db import models
from django.template import Template, Context
from django.conf import settings
from django.utils.html import format_html
from django.utils.module_loading import import_string

from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText

from viberbot import Api, BotConfiguration
from viberbot.api.messages import TextMessage

from .fcm import NotifyDevice

from .choices import TYPE, STATE
from .category import NotifyCategory
from .config import NotifyConfig
from .template import NotifyTemplate
from .file import NotifyFile
from .log import NotifyErrorLog
from .smtp import SMTPAccount
from django.utils.timezone import now
from django.utils.safestring import mark_safe
from ..mixins import UserNotifyMixin


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
                                 verbose_name='Категория')
    event = models.IntegerField(choices=settings.CHOICES_NOTIFY_EVENT, blank=True, null=True, verbose_name='Событие')
    files = models.ManyToManyField(NotifyFile, verbose_name='Файлы')

    is_read = models.BooleanField(default=False, verbose_name='Прочитано')
    data_json = models.TextField(blank=True, null=True, verbose_name='Данные пуш-уведомления (JSON)')

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
            self.phone = self.user.phone
            self.telegram_chat_id = self.user.telegram_chat_id
            self.viber_chat_id = self.user.viber_chat_id

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
            from django.core.mail import EmailMultiAlternatives
            content = self.html or self.text
            msg = EmailMultiAlternatives(self.subject, content, account.sender, [self.email or self.user.email])
            msg.attach_alternative(content, "text/html")
            if msg.send():
                self.state = STATE.DELIVERED
                self.sent_at = now()
            else:
                self.state = STATE.REJECTED
        except Exception as e:  # noqa
            self.state = STATE.REJECTED
            self.to_log(str(e))

    def send_sms(self):
        config = NotifyConfig.get_solo()

        if not config.is_sms_enabled:
            self.state = STATE.DISABLED
            return

        try:
            msg = str(self.text.replace(' ', '+'))
            url = '{url}?msg={text}&to={to}&api_id={api_id}&from={from_text}&json=1'.format(
                url=config.sms_url,
                api_id=config.sms_api_id,
                from_text=config.sms_from,
                to=self.phone,
                text=msg,
            )
            response = requests.get(url)
            response_dict = response.json()
            if response_dict.get('status'):
                self.state = STATE.DELIVERED
                self.sent_at = now()
            else:
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

    @staticmethod
    def send(event, context, user=None, email=None, phone=None, files=None, data_json=None, notify_templates=None,
             viber_chat_id=None):

        from user.models import User

        user_want_message_check = None
        if hasattr(settings, 'NOTIFY_USER_WANT_MESSAGE_CHECK') and settings.NOTIFY_USER_WANT_MESSAGE_CHECK is not None:
            user_want_message_check = import_string(settings.NOTIFY_USER_WANT_MESSAGE_CHECK)

        # Для выбора шаблонов в action'е
        if notify_templates:
            templates = NotifyTemplate.objects.filter(id__in=notify_templates, event=event, is_active=True)
        else:
            templates = NotifyTemplate.objects.filter(event=event, is_active=True)

        if files is None:
            files = []

        data_json = json.dumps(data_json) if data_json is not None else None

        file_instances = []
        for f in files:
            instance = NotifyFile.objects.create(file=f)
            file_instances.append(instance)

        notification_count = 0

        for template in templates:
            # Формируем список основных и дополнительных получателей письма
            # Первого получателя заполняем из шаблона, его данные могут быть пустыми - чтобы можно было через
            # код отправить уведомление
            if template.user or template.email or template.phone or template.viber_chat_id:
                recievers = [{
                    'user': template.user,
                    'email': template.email,
                    'phone': template.phone,
                    'viber_chat_id': template.viber_chat_id,
                }]
            elif user or phone or email or viber_chat_id:
                recievers = [{
                    'user': user,
                    'email': email,
                    'phone': phone,
                    'viber_chat_id': viber_chat_id,
                }]
            else:
                recievers = []

            for user_list in template.user_lists.all():
                for participant in user_list.participants.all():
                    # Если у участника из дополнительного списка ничего не заполнено - не отправляем уведомление
                    if participant.user is not None:
                        recievers.append({
                            'user': participant.user,
                            'email': participant.email,
                            'phone': participant.phone,
                            'viber_chat_id': participant.viber_chat_id,
                        })

                # Если в списке отмечены группы
                if user_list.user_groups and not user_list.mail_to_all:
                    group_users = User.objects.filter(groups__in=list(user_list.user_groups.all()))
                    for user in group_users:
                        recievers.append(
                            {
                                'user': user,
                                'email': user.email,
                                'phone': user.phone,
                                'viber_chat_id': user.viber_chat_id,
                            }
                        )
                    # Убираем дубликаты пользователей
                    recievers = list({v['email']: v for v in recievers}.values())

                # Если в списке пользователей отмечены все пользователи
                if user_list.mail_to_all:
                    recievers = []
                    users = User.objects.all()
                    for user in users:
                        recievers.append(
                            {
                                'user': user,
                                'email': user.email,
                                'phone': user.phone,
                                'viber_chat_id': user.viber_chat_id,
                            }
                        )

            for reciever in recievers:
                template_user = reciever['user']
                template_email = reciever['email']
                template_phone = reciever['phone']
                template_viber_chat_id = reciever['viber_chat_id']
                # Если в шаблоне не указан получатель, то получатель тот, кого передали в коде
                if template_user is None and template_email is None and template_phone is None and template_viber_chat_id is None:
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
                    user_want_message_check(event, template.type, template_user): # noqa
                    continue

                local_context = context.copy()

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
                    phone=template_phone,
                    viber_chat_id=template_viber_chat_id,
                    type=template.type,
                    event=template.event,
                    category=template.category,
                    data_json=data_json,
                    send_at=template.send_at,
                )

                file_instance = instance.files
                for f in file_instances:
                    file_instance.add(f)
                instance.save()
                notification_count += 1

        return notification_count

    def _render_body(self, mail_from, layout):
        msg = MIMEMultipart('alternative')

        msg['Subject'] = self.subject
        msg['From'] = mail_from
        msg['To'] = self.email

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
