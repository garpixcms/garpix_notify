from django.db import models
from django.conf import settings
from django.template import Template, Context

from .choices import TYPE
from .category import NotifyCategory
from .user_list import NotifyUserList

from ckeditor_uploader.fields import RichTextUploadingField
from ..mixins import UserNotifyMixin


class NotifyTemplate(UserNotifyMixin):
    title = models.CharField(max_length=255, verbose_name='Название для админа')
    subject = models.CharField(max_length=255, default='', blank=True, verbose_name='Заголовок')
    text = models.TextField(verbose_name='Текст')
    html = RichTextUploadingField(verbose_name='HTML')

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True, verbose_name='Пользователь (получатель)')
    email = models.EmailField(max_length=255, blank=True, null=True, verbose_name='Email получатель', help_text='Используется только в случае отсутствия указанного пользователя')

    type = models.IntegerField(choices=TYPE.CHOICES, verbose_name='Тип')
    category = models.ForeignKey(NotifyCategory, on_delete=models.CASCADE, related_name='templates', verbose_name='Категория')
    event = models.IntegerField(choices=settings.CHOICES_NOTIFY_EVENT, blank=True, null=True, verbose_name='Событие')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    is_active = models.BooleanField(default=True, verbose_name='Активный')
    send_at = models.DateTimeField(blank=True, null=True, verbose_name='Время начала отправки')

    user_lists = models.ManyToManyField(NotifyUserList, blank=True, verbose_name='Списки пользователей, которые получат копию уведомления')

    def render_subject(self, ct):
        template = Template(self.subject)
        context = Context(ct)
        return template.render(context)

    def render_text(self, ct):
        template = Template(self.text)
        context = Context(ct)
        return template.render(context)

    def render_html(self, ct):
        template = Template(self.html)
        context = Context(ct)
        return template.render(context)

    def get_event_data(self):
        return settings.NOTIFY_EVENTS[self.event]

    def get_context_description(self):
        try:
            text = self.get_event_data()['context_description'] if self.event else '--'
        except:  # noqa
            text = '--'
        return text
    get_context_description.short_description = 'Описание контекста шаблона'

    def get_event_description(self):
        try:
            text = self.get_event_data()['event_description'] if self.event else '--'
        except:  # noqa
            text = '--'
        return text
    get_event_description.short_description = 'Описание события'

    def get_test_data(self):
        try:
            data = self.get_event_data()['test_data'] if self.event else {}
        except:  # noqa
            data = {}
        return data

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Шаблон'
        verbose_name_plural = 'Шаблоны'
