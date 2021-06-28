from django.db import models


class NotifyCategory(models.Model):
    title = models.CharField(max_length=255, verbose_name='Заголовок')
    template = models.TextField(verbose_name='Шаблон', default='{{text}}')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
