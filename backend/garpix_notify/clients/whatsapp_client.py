from django.conf import settings
from django.utils.timezone import now
from django.db import DatabaseError, ProgrammingError

from twilio.rest import Client

from garpix_notify.models.config import NotifyConfig
from garpix_notify.models.choices import STATE
from garpix_notify.utils import ReceivingUsers


class WhatsAppClient:

    def __init__(self, notify):
        self.notify = notify
        try:
            self.config = NotifyConfig.get_solo()
            self.IS_WHATS_APP_ENABLED = self.config.is_whatsapp_enabled
            self.WHATS_APP_AUTH_TOKEN = self.config.whatsapp_auth_token
            self.WHATS_APP_ACCOUNT_SID = self.config.whatsapp_account_sid
            self.WHATS_APP_NUMBER_SENDER = self.config.whatsapp_sender
        except (DatabaseError, ProgrammingError):
            self.IS_WHATS_APP_ENABLED = getattr(settings, 'IS_WHATS_APP_ENABLED', True)
            self.WHATS_APP_AUTH_TOKEN = getattr(settings, 'WHATS_APP_AUTH_TOKEN', None)
            self.WHATS_APP_ACCOUNT_SID = getattr(settings, 'WHATS_APP_ACCOUNT_SID', None)
            self.WHATS_APP_NUMBER_SENDER = getattr(settings, 'WHATS_APP_NUMBER_SENDER', '')

    def __send_message(self):
        if not self.IS_WHATS_APP_ENABLED:
            self.notify.state = STATE.DISABLED
            self.notify.to_log('Not sent (sending is prohibited by settings)')
            return

        client = Client(self.WHATS_APP_ACCOUNT_SID, self.WHATS_APP_AUTH_TOKEN)
        text_massage = self.notify.text
        users_list = self.notify.users_list.all().order_by('-mail_to_all')

        result = False

        try:
            if users_list.exists():
                participants: list = ReceivingUsers.run_receiving_users(users_list, 'phone')
                if participants:
                    for participant in participants:
                        result = client.messages.create(body=text_massage,
                                                        from_=f'whatsapp:{self.WHATS_APP_NUMBER_SENDER}',
                                                        to=f'whatsapp:{participant}')
            else:
                result = client.messages.create(body=text_massage,
                                                from_=f'whatsapp:{self.WHATS_APP_NUMBER_SENDER}',
                                                to=f'whatsapp:{self.notify.phone}')
            if result.sid:
                self.notify.state = STATE.DELIVERED
                self.notify.sent_at = now()
            else:
                self.notify.state = STATE.REJECTED
                self.notify.to_log('REJECTED WITH DATA, please test it.')
        except Exception as e:
            self.notify.state = STATE.REJECTED
            self.notify.to_log(str(e))

    @classmethod
    def send_whatsapp(cls, notify):
        cls(notify).__send_message()
