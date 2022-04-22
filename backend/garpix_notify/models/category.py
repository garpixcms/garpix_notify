from django.db import models
from .template import NotifyTemplate


class NotifyCategory(models.Model):
    title = models.CharField(max_length=255, verbose_name='Заголовок')
    template = models.TextField(verbose_name='Простой шаблон', default='{{text}}')
    template_choice = models.ForeignKey(
        NotifyTemplate,
        on_delete=models.CASCADE,
        related_name='template',
        verbose_name='Выбрать готовый шаблон для категории',
        null=True,
        blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
