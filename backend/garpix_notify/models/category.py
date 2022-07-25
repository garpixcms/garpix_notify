from django.db import models
from django.db.models import Manager


class NotifyCategory(models.Model):
    title = models.CharField(max_length=255, verbose_name='Заголовок')
    template = models.TextField(verbose_name='Шаблон', default='{{text}}')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    objects = Manager()

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
