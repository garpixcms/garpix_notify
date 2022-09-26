from django.conf import settings
from django.utils.timezone import now
from django.db import DatabaseError, ProgrammingError

from viberbot import Api, BotConfiguration
from viberbot.api.messages import TextMessage

from garpix_notify.models.config import NotifyConfig
from garpix_notify.models.choices import STATE
from garpix_notify.utils import ReceivingUsers


class ViberClient:

    def __init__(self, notify):
        self.notify = notify
        try:
            self.config = NotifyConfig.get_solo()
            self.IS_VIBER_ENABLED = self.config.is_viber_enabled
            self.VIBER_API_KEY = self.config.viber_api_key
            self.VIBER_BOT_NAME = self.config.viber_bot_name
        except (DatabaseError, ProgrammingError):
            self.IS_VIBER_ENABLED = getattr(settings, 'IS_VIBER_ENABLED', True)
            self.VIBER_API_KEY = getattr(settings, 'VIBER_API_KEY', '000000000:AAAAAAAAAA-AAAAAAAA-_AAAAAAAAAAAAAA')
            self.VIBER_BOT_NAME = getattr(settings, 'VIBER_BOT_NAME', 'MySuperBot')

    def __send_viber_client(self):
        if not self.IS_VIBER_ENABLED:
            self.notify.state = STATE.DISABLED
            self.notify.to_log('Not sent (sending is prohibited by settings)')
            return

        text = self.notify.text
        users_list = self.notify.users_list.all().order_by('-mail_to_all')

        viber = Api(BotConfiguration(
            name=self.VIBER_BOT_NAME,
            avatar='',
            auth_token=self.VIBER_API_KEY
        ))
        try:
            result = False
            if users_list.exists():
                participants: list = ReceivingUsers.run_receiving_users(users_list, 'viber_chat_id')
                if participants:
                    for participant in participants:
                        result = viber.send_messages(to=participant, messages=[TextMessage(text=text)])
                # если не добавлены, сообщение приходит пользователю(получателю) или тому, кто указан в коде
            else:
                result = viber.send_messages(to=self.notify.viber_chat_id, messages=[TextMessage(text=text)])
            if result:
                self.notify.state = STATE.DELIVERED
                self.notify.sent_at = now()
            else:
                self.notify.state = STATE.REJECTED
                self.notify.to_log('REJECTED WITH DATA, please test it.')
        except Exception as e:
            self.notify.state = STATE.REJECTED
            self.notify.to_log(str(e))

    @classmethod
    def send_viber(cls, notify):
        cls(notify).__send_viber_client()
