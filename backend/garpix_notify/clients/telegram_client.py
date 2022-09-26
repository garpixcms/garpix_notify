from django.conf import settings
from django.utils.timezone import now
from django.db import DatabaseError, ProgrammingError

from garpix_notify.models.config import NotifyConfig
from garpix_notify.models.choices import STATE


class TelegramClient:

    def __init__(self, notify):
        self.notify = notify
        try:
            self.config = NotifyConfig.get_solo()
            self.IS_TELEGRAM_ENABLED = self.config.is_telegram_enabled
            self.TELEGRAM_API_KEY = self.config.telegram_api_key
            self.TELEGRAM_PARSE_MODE = self.config.telegram_parse_mode
            self.TELEGRAM_DISABLE_NOTIFICATION = self.config.telegram_disable_notification
            self.TELEGRAM_DISABLE_PAGE_PREVIEW = self.config.telegram_disable_web_page_preview
            self.TELEGRAM_SENDING_WITHOUT_REPLY = self.config.telegram_allow_sending_without_reply
            self.TELEGRAM_TIMEOUT = self.config.telegram_timeout
        except (DatabaseError, ProgrammingError):
            self.IS_TELEGRAM_ENABLED = True
            self.TELEGRAM_PARSE_MODE = getattr(settings, 'TELEGRAM_PARSE_MODE', None)
            self.TELEGRAM_DISABLE_NOTIFICATION = getattr(settings, 'TELEGRAM_DISABLE_NOTIFICATION', False)
            self.TELEGRAM_DISABLE_PAGE_PREVIEW = getattr(settings, 'TELEGRAM_DISABLE_PAGE_PREVIEW', False)
            self.TELEGRAM_SENDING_WITHOUT_REPLY = getattr(settings, 'TELEGRAM_SENDING_WITHOUT_REPLY', False)
            self.TELEGRAM_TIMEOUT = getattr(settings, 'TELEGRAM_TIMEOUT', None)
            self.TELEGRAM_API_KEY = getattr(settings, 'TELEGRAM_API_KEY', '000000000:AAAAAAAAAA-AAAAAAAA-_AAAAAAAAAAAAAA')

    def __chunks(self, s, n):
        """Produce `n`-character chunks from `s`."""
        for start in range(0, len(s), n):
            yield s[start:start + n]

    def __send_telegram_client(self):
        import telegram

        if not self.IS_TELEGRAM_ENABLED:
            self.notify.state = STATE.DISABLED
            self.notify.to_log('Not sent (sending is prohibited by settings)')
            return

        bot = telegram.Bot(token=self.TELEGRAM_API_KEY)
        parse_mode = self.TELEGRAM_PARSE_MODE if self.TELEGRAM_PARSE_MODE != '' else None

        try:
            result = False
            for chunk in self.__chunks(str(self.notify.text), 4096):
                result = bot.sendMessage(chat_id=self.notify.telegram_chat_id,
                                         text=chunk,
                                         parse_mode=parse_mode,
                                         disable_web_page_preview=self.TELEGRAM_DISABLE_PAGE_PREVIEW,
                                         disable_notification=self.TELEGRAM_DISABLE_NOTIFICATION,
                                         timeout=self.TELEGRAM_TIMEOUT,
                                         allow_sending_without_reply=self.TELEGRAM_SENDING_WITHOUT_REPLY)
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
    def send_telegram(cls, notify):
        cls(notify).__send_telegram_client()
