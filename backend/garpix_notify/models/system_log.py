from django.db import models


class SystemNotifyErrorLog(models.Model):
    notify = models.ForeignKey('garpix_notify.SystemNotify', on_delete=models.CASCADE, related_name='logs',
                               verbose_name='SystemNotify')
    error = models.TextField(verbose_name='Ошибка', blank=True, null=True, default='')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    def __str__(self):
        return '{}: {}'.format(self.pk, self.created_at.strftime('%d.%m.%Y %h:%M:%s'))

    class Meta:
        verbose_name = 'Лог отправки системного уведомления'
        verbose_name_plural = 'Логи отправки системных уведомлений'
