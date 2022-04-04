from django.db import models
from solo.models import SingletonModel


class NotifyConfig(SingletonModel):
    class SMS_URL:
        """
        URL СМС провайдера
        """

        SMSRU_ID = 0
        WEBSZK_ID = 1

        SMSRU_URL = 'http://sms.ru/send/'
        WEBSZK_URL = 'http://gateway.api.sc/get/'

        TYPES = (
            (SMSRU_ID, 'sms.ru'),
            (WEBSZK_ID, 'web.szk-info.ru'),
        )

    periodic = models.IntegerField(default=60, verbose_name='Периодичность отправки уведомлений (сек.)')

    email_max_day_limit = models.IntegerField(default=240, verbose_name='Дневной лимит отправки писем')
    email_max_hour_limit = models.IntegerField(default=40, verbose_name='Часовой лимит отправки писем')

    sms_url_type = models.IntegerField(default=SMS_URL.SMSRU_ID, choices=SMS_URL.TYPES, verbose_name='URL СМС провайдера')
    sms_api_id = models.CharField(default='1234567890', blank=True, max_length=255,
                                  verbose_name='API ID СМС провайдера')
    sms_login = models.CharField(default='', blank=True, max_length=255,
                                 verbose_name='Логин пользователя СМС провайдера')
    sms_password = models.CharField(default='', blank=True, max_length=255,
                                    verbose_name='Пароль для api СМС провайдера')
    sms_from = models.CharField(default='', blank=True, max_length=255, verbose_name='Отправитель СМС',
                                help_text='Например, Garpix')

    telegram_api_key = models.CharField(default='000000000:AAAAAAAAAA-AAAAAAAA-_AAAAAAAAAAAAAA', blank=True,
                                        max_length=255, verbose_name='Telegram API Key')
    telegram_bot_name = models.CharField(default='', blank=True, help_text='Например, MySuperBot',
                                         max_length=255, verbose_name='Telegram Имя бота')
    telegram_welcome_text = models.TextField(blank=True,
                                             default='Добрый день! Здесь вы можете получать уведомления от нашего сайта',
                                             verbose_name='Telegram - Приветственный текст бота')
    telegram_help_text = models.TextField(blank=True,
                                          default='Используйте команду /set <уникальный код> для того, чтобы получать сообщения от бота. Уникальный код вы можете получить на нашем сайте',
                                          verbose_name='Telegram - Текст помощи бота')
    telegram_bad_command_text = models.TextField(blank=True,
                                                 default='Неправильный формат команды',
                                                 verbose_name='Telegram - Текст неправильной команды бота')
    telegram_success_added_text = models.TextField(blank=True,
                                                   default='Ваша учетная запись успешно привязана к боту. Вы будете получать уведомления!',
                                                   verbose_name='Telegram - Текст успешно добавлен код')
    telegram_failed_added_text = models.TextField(blank=True,
                                                  default='Ошибка при привязке учетной записи. Пожалуйста, свяжитесь с техподдержкой',
                                                  verbose_name='Telegram - Текст провал, не добавлен код')
    viber_api_key = models.CharField(default='000000000:AAAAAAAAAA-AAAAAAAA-_AAAAAAAAAAAAAA', blank=True,
                                     max_length=255, verbose_name='Viber API Key')
    viber_bot_name = models.CharField(blank=True, max_length=255, verbose_name='Название viber бота',
                                      default='Viber bot')
    is_email_enabled = models.BooleanField(default=True, verbose_name='Разрешить отправку Email')
    is_sms_enabled = models.BooleanField(default=True, verbose_name='Разрешить отправку SMS')
    is_push_enabled = models.BooleanField(default=True, verbose_name='Разрешить отправку PUSH')
    is_telegram_enabled = models.BooleanField(default=True, verbose_name='Разрешить отправку Telegram',
                                              help_text='Внимание! Telegram недоступен на серверах на территории РФ и работать на них не будет!.')
    is_viber_enabled = models.BooleanField(default=True, verbose_name='Разрешить отправку Viber')

    viber_success_added_text = models.TextField(blank=True,
                                                default='Ваша учетная запись успешно привязана к боту. Вы будете получать уведомления!',
                                                verbose_name='Viber - Текст успешно добавлен код')
    viber_failed_added_text = models.TextField(blank=True,
                                               default='Ошибка при привязке учетной записи. Пожалуйста, свяжитесь с техподдержкой',
                                               verbose_name='Viber - Текст провал, не добавлен код')

    viber_text_for_new_sub = models.TextField(blank=True,
                                              default='cпасибо за подписку, Введите secret_key чтобы получать сообщения от бота.',
                                              verbose_name='Viber - Текст  для новых подписчиков')

    viber_welcome_text = models.TextField(blank=True,
                                          default='для активации бота нужно отправить любое сообщения',
                                          verbose_name='Viber - Приветственный текст бота')

    class Meta:
        verbose_name = 'Настройка'
        verbose_name_plural = 'Настройки'
