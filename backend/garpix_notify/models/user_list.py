from django.db import models
from django.contrib.auth.models import Group


class NotifyUserList(models.Model):
    title = models.CharField(max_length=255, verbose_name='Название списка пользователей')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    user_groups = models.ManyToManyField(Group, blank=True, verbose_name='Группы пользователей')
    mail_to_all = models.BooleanField(default=False, verbose_name='Отправить всем')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Список пользователей для рассылки'
        verbose_name_plural = 'Списки пользователей для рассылки'
