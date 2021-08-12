from django.db import models
from solo.models import SingletonModel


class NotifyConfig(SingletonModel):
    periodic = models.IntegerField(default=60, verbose_name='Периодичность отправки уведомлений (сек.)')

    email_max_day_limit = models.IntegerField(default=240, verbose_name='Дневной лимит отправки писем')
    email_max_hour_limit = models.IntegerField(default=40, verbose_name='Часовой лимит отправки писем')

    sms_url = models.CharField(default='http://sms.ru/sms/send', max_length=255, verbose_name='URL СМС провайдера')
    sms_api_id = models.CharField(default='1234567890', blank=True, max_length=255,
                                  verbose_name='API ID СМС провайдера')
    sms_from = models.CharField(default='', blank=True, max_length=255, verbose_name='Отправитель СМС',
                                help_text='Например, Garpix')

    telegram_api_key = models.CharField(default='000000000:AAAAAAAAAA-AAAAAAAA-_AAAAAAAAAAAAAA', blank=True,
                                        max_length=255, verbose_name='Telegram API Key')
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
