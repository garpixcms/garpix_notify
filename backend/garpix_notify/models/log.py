from django.db import models


class NotifyErrorLog(models.Model):
    notify = models.ForeignKey('garpix_notify.Notify', on_delete=models.CASCADE, related_name='logs', verbose_name='Notify')
    error = models.TextField(verbose_name='Ошибка', blank=True, null=True, default='')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    def __str__(self):
        return '{}: {})'.format(self.id, self.created_at.strftime('%d.%m.%Y %h:%M:%s'))

    class Meta:
        verbose_name = 'Ошибка отправки уведомления'
        verbose_name_plural = 'Ошибки отправки уведомления'
