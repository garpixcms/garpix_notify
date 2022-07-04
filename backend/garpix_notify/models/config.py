from django.db import models
from solo.models import SingletonModel

from garpix_notify.models.choices import EMAIL_MALLING, PARSE_MODE_TELEGRAM, SMS_URL, CALL_URL


class NotifyConfig(SingletonModel):
    periodic = models.IntegerField(default=60, verbose_name='Периодичность отправки уведомлений (сек.)')

    email_max_day_limit = models.IntegerField(default=240, verbose_name='Дневной лимит отправки писем')
    email_max_hour_limit = models.IntegerField(default=40, verbose_name='Часовой лимит отправки писем')

    sms_url_type = models.IntegerField(default=SMS_URL.SMSRU_ID, choices=SMS_URL.TYPES,
                                       verbose_name='URL СМС провайдера')
    sms_api_id = models.CharField(default='1234567890', blank=True, max_length=255,
                                  verbose_name='API ID СМС провайдера')
    sms_login = models.CharField(default='', blank=True, max_length=255,
                                 verbose_name='Логин пользователя СМС провайдера')
    sms_password = models.CharField(default='', blank=True, max_length=255,
                                    verbose_name='Пароль для api СМС провайдера')
    sms_from = models.CharField(default='', blank=True, max_length=255, verbose_name='Отправитель СМС',
                                help_text='Например, Garpix')
    call_url_type = models.IntegerField(default=CALL_URL.SMSRU_CALL_API_ID, choices=CALL_URL.TYPES,
                                        verbose_name='URL звонка провайдера')
    call_api_id = models.CharField(default='1234567890', blank=True, max_length=255,
                                   verbose_name='API ID оператора связи')
    call_login = models.CharField(default='', blank=True, max_length=255,
                                  verbose_name='Логин/Индетификатор сервиса оператора связи')
    call_password = models.CharField(default='', blank=True, max_length=255,
                                     verbose_name='Пароль/Секретный ключ оператора связи')
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
    telegram_parse_mode = models.CharField(default=PARSE_MODE_TELEGRAM.EMPTY, choices=PARSE_MODE_TELEGRAM.TYPES,
                                           verbose_name='Тип парсера телеграм сообщений', max_length=100, blank=True)
    telegram_disable_notification = models.BooleanField(verbose_name='Пользователи получат уведомление без звука',
                                                        default=False)
    telegram_disable_web_page_preview = models.BooleanField(
        verbose_name='Отключает предварительный просмотр ссылок в сообщениях',
        default=False)
    telegram_allow_sending_without_reply = models.BooleanField(
        verbose_name='Разрешить, если сообщение должно быть отправлено, даже если ответное сообщение не найдено',
        default=False)
    telegram_timeout = models.FloatField(default=None, blank=True, verbose_name="Тайм-аут чтения с сервера", null=True)
    viber_api_key = models.CharField(default='000000000:AAAAAAAAAA-AAAAAAAA-_AAAAAAAAAAAAAA', blank=True,
                                     max_length=255, verbose_name='Viber API Key')
    viber_bot_name = models.CharField(blank=True, max_length=255, verbose_name='Название viber бота',
                                      default='Viber bot')
    whatsapp_sender = models.CharField(max_length=30, blank=True, default='',
                                       verbose_name='Телефон отправителя WhatsApp')
    whatsapp_auth_token = models.CharField(default='XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX', blank=True,
                                           max_length=255, verbose_name='WhatsApp Auth Token')
    whatsapp_account_sid = models.CharField(default='ACXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX', blank=True,
                                            max_length=255, verbose_name='WhatsApp Account SID')
    is_email_enabled = models.BooleanField(default=True, verbose_name='Разрешить отправку Email')
    is_sms_enabled = models.BooleanField(default=True, verbose_name='Разрешить отправку SMS')
    is_call_enabled = models.BooleanField(default=True, verbose_name='Разрешить отправку звонков')
    is_push_enabled = models.BooleanField(default=True, verbose_name='Разрешить отправку PUSH')
    is_telegram_enabled = models.BooleanField(default=True, verbose_name='Разрешить отправку Telegram')
    is_viber_enabled = models.BooleanField(default=True, verbose_name='Разрешить отправку Viber')
    is_whatsapp_enabled = models.BooleanField(default=True, verbose_name='Разрешить отправку WhatsApp')

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
    email_malling = models.IntegerField(default=EMAIL_MALLING.BCC, choices=EMAIL_MALLING.TYPES,
                                        verbose_name='Тип массовой рассылки',
                                        help_text='Если выбрана обычная рассылка, то пользователи будут видеть email друг друга')

    class Meta:
        verbose_name = 'Настройка'
        verbose_name_plural = 'Настройки'

    def __str__(self):
        return 'Настройки'
