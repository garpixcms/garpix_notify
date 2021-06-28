from django.db import models


class UserNotifyMixin(models.Model):
    phone = models.CharField(max_length=30, blank=True, default='', verbose_name='Телефон')
    telegram_chat_id = models.CharField(max_length=200, blank=True, default='',
                                        verbose_name='Telegram ID пользователя/чата')
    viber_chat_id = models.CharField(max_length=200, blank=True, default='',
                                     verbose_name='Viber ID пользователя/чата')
    viber_secret_key = models.CharField(max_length=200, blank=True, default='',
                                        verbose_name='Ключ подключения Viber')

    class Meta:
        abstract = True
