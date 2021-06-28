from django.db import models
from django.utils.timezone import now, timedelta
from django.utils.html import format_html
from .category import NotifyCategory
from .config import NotifyConfig


class SMTPAccount(models.Model):
    host = models.CharField(default='smtp.yandex.ru', max_length=255, verbose_name='Хост')
    port = models.IntegerField(default=587, verbose_name='Порт')
    is_use_tls = models.BooleanField(default=True, verbose_name='Использовать TLS?')
    is_use_ssl = models.BooleanField(default=False, verbose_name='Использовать SSL?')
    sender = models.EmailField(max_length=255, blank=True, default='', verbose_name='Отправитель')
    username = models.CharField(max_length=255, blank=True, default='', verbose_name='Имя пользователя')
    password = models.CharField(max_length=255, blank=True, default='', verbose_name='Пароль пользователя')
    timeout = models.IntegerField(default=5000, verbose_name='Таймаут (сек.)')
    category = models.ForeignKey(NotifyCategory, on_delete=models.CASCADE, related_name='accounts', verbose_name='Тип')

    is_active = models.BooleanField(default=True, verbose_name='Включить аккаунт')

    email_hour_used_times = models.IntegerField(default=0, verbose_name='Количество использований в час')
    email_day_used_times = models.IntegerField(default=0, verbose_name='Количество использований в день')
    email_hour_used_date = models.DateTimeField(default=now, verbose_name='Дата использований в час')
    email_day_used_date = models.DateTimeField(default=now, verbose_name='Дата использований в день')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    @classmethod
    def get_free_smtp(cls):
        """
        Проверяет и отдает один аакаунт SMTP, с которого можно отправить письмо
        """
        config = NotifyConfig.objects.get()
        Q = models.Q

        hour_limit = now() - timedelta(hours=1)
        day_limit = now() - timedelta(days=1)

        account = cls.objects \
            .filter(Q(email_hour_used_times__lt=config.email_max_hour_limit)) \
            .filter(Q(email_day_used_times__lt=config.email_max_day_limit)) \
            .filter(Q(is_active=True)) \
            .distinct() \
            .first()

        if account is None:
            return None

        account.email_hour_used_times += 1
        account.email_day_used_times += 1

        if account.email_hour_used_date < hour_limit:
            account.email_hour_used_date = now()
            account.email_hour_used_times = 1

        if account.email_day_used_date < day_limit:
            account.email_day_used_date = now()
            account.email_day_used_times = 1

        account.save()
        return account

    def is_worked_now(self):
        config = NotifyConfig.objects.get()
        hour_limit = now() - timedelta(hours=1)
        day_limit = now() - timedelta(days=1)

        if self.email_day_used_times >= config.email_max_day_limit and self.email_day_used_date > day_limit:
            return format_html('<span style="color:red;">Превышен суточный лимит</span>')
        elif not self.is_active:
            return format_html('<span style="color:red;">Отключен</span>')
        elif self.email_hour_used_times >= config.email_max_hour_limit and self.email_hour_used_date > hour_limit:
            return format_html('<span style="color:orange;">Превышен часовой лимит</span>')
        else:
            return format_html('<span style="color:green;">Включен</span>')

    is_worked_now.short_description = 'Состояние'

    def __str__(self):
        return '{} ({}:{})'.format(self.username, self.host, self.port)

    def clear(self):
        self.email_hour_used_times = 0
        self.email_day_used_times = 0
        self.email_hour_used_date = now()
        self.email_day_used_date = now()
        self.save()

    class Meta:
        verbose_name = 'SMTP аккаунт'
        verbose_name_plural = 'SMTP аккаунты'
