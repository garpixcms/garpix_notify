from django.db import models
import uuid


def generate_uuid():
    return uuid.uuid4().hex


TELEGRAM_CONNECT_USER_HELP = """Для получения уведомлений в Telegram вам необходимо:
1. Отправить боту https://t.me/{telegram_bot_name} сообщение /start:
2. Отправить ему сообщение /set {telegram_secret}
3. Все, вы будете получать уведомления.
"""


class UserNotifyMixin(models.Model):
    phone = models.CharField(max_length=30, blank=True, default='', verbose_name='Телефон')
    telegram_chat_id = models.CharField(max_length=200, blank=True, default='',
                                        verbose_name='Telegram ID пользователя/чата')
    telegram_secret = models.CharField(max_length=150, unique=True, default=generate_uuid,
                                       verbose_name='Ключ подключения Telegram')
    viber_chat_id = models.CharField(max_length=200, blank=True, default='',
                                     verbose_name='Viber ID пользователя/чата')
    viber_secret_key = models.CharField(max_length=200, blank=True, default='',
                                        verbose_name='Ключ подключения Viber')

    def get_telegram_connect_user_help(self):
        from ..models.config import NotifyConfig
        config = NotifyConfig.get_solo()
        return TELEGRAM_CONNECT_USER_HELP.format(
            telegram_secret=self.telegram_secret,
            telegram_bot_name=config.telegram_bot_name,
        )
    get_telegram_connect_user_help.short_description = 'Как подключить Telegram-уведомления'

    class Meta:
        abstract = True
