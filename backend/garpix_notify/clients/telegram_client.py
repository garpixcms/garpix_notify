from django.conf import settings
from django.utils.timezone import now

from garpix_notify.models.config import NotifyConfig
from garpix_notify.models.choices import STATE


try:
    config = NotifyConfig.get_solo()
    IS_TELEGRAM_ENABLED = config.is_telegram_enabled
    TELEGRAM_API_KEY = config.telegram_api_key
    TELEGRAM_PARSE_MODE = config.telegram_parse_mode
    TELEGRAM_DISABLE_NOTIFICATION = config.telegram_disable_notification
    TELEGRAM_DISABLE_PAGE_PREVIEW = config.telegram_disable_web_page_preview
    TELEGRAM_SENDING_WITHOUT_REPLY = config.telegram_allow_sending_without_reply
    TELEGRAM_TIMEOUT = config.telegram_timeout
except Exception:
    IS_TELEGRAM_ENABLED = True
    TELEGRAM_PARSE_MODE = getattr(settings, 'TELEGRAM_PARSE_MODE', None)
    TELEGRAM_DISABLE_NOTIFICATION = getattr(settings, 'TELEGRAM_DISABLE_NOTIFICATION', False)
    TELEGRAM_DISABLE_PAGE_PREVIEW = getattr(settings, 'TELEGRAM_DISABLE_PAGE_PREVIEW', False)
    TELEGRAM_SENDING_WITHOUT_REPLY = getattr(settings, 'TELEGRAM_SENDING_WITHOUT_REPLY', False)
    TELEGRAM_TIMEOUT = getattr(settings, 'TELEGRAM_TIMEOUT', None)
    TELEGRAM_API_KEY = getattr(settings, 'TELEGRAM_API_KEY', '000000000:AAAAAAAAAA-AAAAAAAA-_AAAAAAAAAAAAAA')


class TelegramClient:

    def __init__(self, notify):
        self.notify = notify

    def __chunks(self, s, n):
        """Produce `n`-character chunks from `s`."""
        for start in range(0, len(s), n):
            yield s[start:start + n]

    def __send_telegram_client(self):
        import telegram
        bot = telegram.Bot(token=TELEGRAM_API_KEY)
        parse_mode = TELEGRAM_PARSE_MODE if TELEGRAM_PARSE_MODE != '' else None
        if not IS_TELEGRAM_ENABLED:
            self.state = STATE.DISABLED
            return

        try:
            result = False
            for chunk in self.__chunks(str(self.notify.text), 4096):
                result = bot.sendMessage(chat_id=self.notify.telegram_chat_id,
                                         text=chunk,
                                         parse_mode=parse_mode,
                                         disable_web_page_preview=TELEGRAM_DISABLE_PAGE_PREVIEW,
                                         disable_notification=TELEGRAM_DISABLE_NOTIFICATION,
                                         timeout=TELEGRAM_TIMEOUT,
                                         allow_sending_without_reply=TELEGRAM_SENDING_WITHOUT_REPLY)
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
