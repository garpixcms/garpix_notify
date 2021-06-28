from django.db import models
from .user_list import NotifyUserList
from django.conf import settings
from ..mixins import UserNotifyMixin


class NotifyUserListParticipant(UserNotifyMixin):
    user_list = models.ForeignKey(NotifyUserList, on_delete=models.CASCADE, related_name='participants', verbose_name='Список пользователей для рассылки')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True, on_delete=models.SET_NULL,
                             related_name='user_lists', verbose_name='Пользователь (получатель)')
    email = models.EmailField(max_length=255, blank=True, null=True, verbose_name='Email Получателя',
                              help_text='Используется только в случае отсутствия указанного пользователя')

    def __str__(self):
        return 'Участник рассылки'

    class Meta:
        verbose_name = 'Участник списка пользователей'
        verbose_name_plural = 'Участники списка пользователей'
