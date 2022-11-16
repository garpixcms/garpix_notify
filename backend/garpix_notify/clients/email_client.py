from smtplib import SMTP, SMTP_SSL

from email.header import Header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

from django.conf import settings
from django.utils.timezone import now
from django.utils.safestring import mark_safe
from django.template import Template, Context
from django.db import DatabaseError, ProgrammingError

from garpix_notify.models.choices import STATE, EMAIL_MALLING
from garpix_notify.models.category import NotifyCategory
from garpix_notify.models.config import NotifyConfig
from garpix_notify.models.smtp import SMTPAccount
from garpix_notify.utils import ReceivingUsers


class EmailClient:

    def __init__(self, notify):
        self.emails: list = []
        self.notify = notify
        try:
            self.config = NotifyConfig.get_solo()
            self.IS_EMAIL_ENABLED = self.config.is_email_enabled
            self.EMAIL_MALLING_TYPE = self.config.email_malling
        except (DatabaseError, ProgrammingError):
            self.IS_EMAIL_ENABLED = getattr(settings, 'IS_EMAIL_ENABLED', True)
            self.EMAIL_MALLING_TYPE = getattr(settings, 'EMAIL_MALLING', EMAIL_MALLING.BCC)

    def __render_body(self, mail_from: str, layout: NotifyCategory, emails: list) -> MIMEMultipart:
        # =============================== Основная часть письма ===========================================
        msg = MIMEMultipart('mixed')
        if len(emails) > 1:
            if self.EMAIL_MALLING_TYPE == EMAIL_MALLING.BCC:
                msg['BCC'] = ', '.join(emails)
            else:
                msg['СС'] = ', '.join(emails)
        else:
            msg['To'] = ''.join(emails)

        msg['Subject'] = Header(self.notify.subject, 'utf-8')
        msg['From'] = mail_from

        if self.notify.files.exists():
            for fl in self.notify.files.all():
                file_name = fl.file.name.split('/')[-1]
                with fl.file.open(mode='rb') as f:
                    part = MIMEApplication(
                        f.read(),
                        Name=file_name
                    )

                part['Content-Disposition'] = 'attachment; filename="%s"' % file_name

                msg.attach(part)

        # =============================== Часть письма с текстом ==========================================
        msg_text = MIMEMultipart('alternative')
        text = MIMEText(self.notify.text, 'plain', 'utf-8')
        msg_text.attach(text)

        if self.notify.html:
            template = Template(layout.template)
            context = Context({'text': mark_safe(self.notify.html)})
            html = MIMEText(mark_safe(template.render(context)), 'html', 'utf-8')
            msg_text.attach(html)

        msg.attach(msg_text)

        return msg

    def __send_email_client(self) -> None:

        if not self.IS_EMAIL_ENABLED:
            self.notify.state = STATE.DISABLED
            self.notify.to_log('Not sent (sending is prohibited by settings)')
            return

        account = SMTPAccount.get_free_smtp()

        if account is None:
            self.notify.state = STATE.DISABLED
            self.notify.to_log('No SMTPAccount')
            return

        if self.notify.sender_email is None:
            self.notify.sender_email = account.sender

        users_list = self.notify.users_list.all().order_by('-mail_to_all')

        if users_list.exists():
            self.emails: list = ReceivingUsers.run_receiving_users(users_list, 'email')

        if self.notify.email:
            self.emails.append(self.notify.email)

        try:
            body = self.__render_body(mail_from=account.sender, layout=self.notify.category, emails=self.emails)
            server = SMTP_SSL(account.host, account.port) if account.is_use_ssl else SMTP(account.host, account.port)
            server.ehlo()
            if account.is_use_tls:
                server.starttls()
            server.login(account.username, account.password)
            server.sendmail(account.sender, self.emails, body.as_string())
            server.close()
            self.notify.state = STATE.DELIVERED
            self.notify.sent_at = now()
        except Exception as e:
            self.notify.state = STATE.REJECTED
            self.notify.to_log(str(e))

    @classmethod
    def send_email(cls, notify) -> None:
        cls(notify).__send_email_client()
