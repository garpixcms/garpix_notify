from django.conf import settings
from django.utils.timezone import now

from viberbot import Api, BotConfiguration
from viberbot.api.messages import TextMessage

from garpix_notify.models.config import NotifyConfig
from garpix_notify.models.choices import STATE
from garpix_notify.utils import ReceivingUsers

try:
    config = NotifyConfig.get_solo()
    IS_VIBER_ENABLED = config.is_viber_enabled
    VIBER_API_KEY = config.viber_api_key
    VIBER_BOT_NAME = config.viber_bot_name
except Exception:
    IS_VIBER_ENABLED = True
    VIBER_API_KEY = getattr(settings, 'VIBER_API_KEY', '000000000:AAAAAAAAAA-AAAAAAAA-_AAAAAAAAAAAAAA')
    VIBER_BOT_NAME = getattr(settings, 'VIBER_BOT_NAME', 'MySuperBot')


class ViberClient:

    def __init__(self, notify):
        self.notify = notify

    def __send_viber_client(self):
        if not IS_VIBER_ENABLED:
            self.notify.state = STATE.DISABLED
            return
        text = self.notify.text
        users_list = self.notify.users_list.all()

        viber = Api(BotConfiguration(
            name=VIBER_BOT_NAME,
            avatar='',
            auth_token=VIBER_API_KEY
        ))
        try:
            result = False
            if users_list.exists():
                participants = ReceivingUsers.run_receiving_users(users_list, value='viber_chat_id')
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
        except Exception as e:  # noqa
            self.notify.state = STATE.REJECTED
            self.notify.to_log(str(e))

    @classmethod
    def send_viber(cls, notify):
        cls(notify).__send_viber_client()
