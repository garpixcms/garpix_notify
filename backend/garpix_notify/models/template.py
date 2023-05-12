import os
import shutil
from pathlib import Path
from typing import Optional, List

from django.core.exceptions import ValidationError
from django.db import models
from django.conf import settings
from django.db.models import Manager
from django.template import Template, Context

from .category import NotifyCategory
from .choices import TYPE
from .user_list import NotifyUserList

from ckeditor_uploader.fields import RichTextUploadingField
from ..mixins import UserNotifyMixin
from ..utils import get_file_path
from ..utils.validators import validate_zip, validate_zip_files
import zipfile
import rarfile
from garpix_utils.file import get_secret_path


class NotifyTemplate(UserNotifyMixin):
    class HTMLFormType(models.TextChoices):
        CKEDITOR = ('ckeditor', 'Визуальный редактор')
        ZIPFILE = ('zipfile', 'Загрузка из архива')

    title = models.CharField(max_length=255, verbose_name='Название для админа')
    subject = models.CharField(max_length=255, default='', blank=True, verbose_name='Заголовок')
    is_delete_after = models.BooleanField(default=False, verbose_name='Удалять после отправки')
    text = models.TextField(verbose_name='Текст')

    html_from_type = models.TextField(max_length=8, choices=HTMLFormType.choices, default=HTMLFormType.CKEDITOR,
                                      verbose_name='Способ формирования html')
    html = RichTextUploadingField(verbose_name='HTML', blank=True)
    zipfile = models.FileField(upload_to=get_file_path, blank=True, null=True, validators=[validate_zip],
                               verbose_name='Файл архива',
                               help_text="Поддерживаются архивы в форматах ZIP и RAR с единственным HTML-файлом и ассетами изображений по относительному или абсолютному пути")

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True,
                             verbose_name='Пользователь (получатель)')
    email = models.EmailField(max_length=255, blank=True, null=True, verbose_name='Email получатель',
                              help_text='Используется только в случае отсутствия указанного пользователя')

    type = models.IntegerField(choices=TYPE.CHOICES, verbose_name='Тип')
    category = models.ForeignKey(NotifyCategory, on_delete=models.CASCADE, related_name='templates',
                                 verbose_name='Категория')
    event = models.IntegerField(choices=settings.CHOICES_NOTIFY_EVENT, blank=True, null=True, verbose_name='Событие')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    is_active = models.BooleanField(default=True, verbose_name='Активный')
    send_at = models.DateTimeField(blank=True, null=True, verbose_name='Время начала отправки')

    user_lists = models.ManyToManyField(NotifyUserList, blank=True, verbose_name='Списки пользователей для рассылки')

    objects = Manager()

    def __str__(self):
        return self.title

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

    @staticmethod
    def get_blank_events_message() -> Optional[str]:
        """ Метод возвращает сообщение о том, что есть Ивенты без шаблонов. """
        message: Optional[str] = None
        events = settings.NOTIFY_EVENTS.keys()
        notify_templates_events = NotifyTemplate.objects.filter(is_active=True).values_list('event', flat=True)
        events_without_templates: List[Optional[int]] = [
            settings.NOTIFY_EVENTS.get(event_id) for event_id in events if event_id not in notify_templates_events
        ]
        if events_without_templates:
            names_events_without_templates: str = ', '.join(
                map(lambda event: event.get('title'), events_without_templates)
            )
            message = 'Не найдено активных шаблонов для ивентов: ' + names_events_without_templates
        return message

    def _parse_and_validate_zipfile(self):

        def _parse_dir(dir_path, imgs, current_folder, root_folders: list):
            for _name in os.listdir(dir_path):
                file_path = os.path.join(dir_path, _name)
                if _name not in ['__MACOSX', '.DS_Store']:
                    if os.path.isdir(file_path):
                        _parse_dir(file_path, imgs, os.path.join(current_folder, _name), root_folders)
                    else:
                        with open(file_path, 'r') as f:
                            validate_zip_files(f)
                            if Path(f.name).suffix[1:].lower() not in ['html', 'htm']:
                                html_path = current_folder
                                if any(root_folders):
                                    _current_folders = current_folder.split('/')
                                    _ci = 0
                                    for _item in root_folders:
                                        if len(_current_folders) == _ci or _current_folders[_ci] != _item:
                                            _current_folders.insert(_ci, '..')
                                        else:
                                            _current_folders[_ci] = None
                                        _ci += 1
                                    html_path = '/'.join([_item for _item in _current_folders if _item is not None])

                                rel_file_path = file_path.split('/')[-1]
                                imgs.append({
                                    'html_path': os.path.join(html_path, rel_file_path),
                                    'file_path': os.path.join(current_folder, rel_file_path)
                                })

        def _validate_and_find_html(dir_path, html_path, root_folder, current_folder) -> (str, str):
            for _name in os.listdir(dir_path):
                file_path = os.path.join(dir_path, _name)
                if _name not in ['__MACOSX', '.DS_Store']:
                    if os.path.isdir(file_path):
                        html_path, root_folder = _validate_and_find_html(file_path, html_path, root_folder,
                                                                         os.path.join(current_folder, _name))
                    else:
                        with open(file_path, 'r') as f:
                            validate_zip_files(f)
                            if Path(f.name).suffix[1:].lower() in ['html', 'htm']:
                                if html_path:
                                    raise ValidationError(
                                        {'zipfile': 'Архив должен содержать только один html файл'})
                                html_path = file_path
                                root_folder = current_folder
            return html_path, root_folder

        try:
            archive = zipfile.ZipFile(self.zipfile, 'r')
        except zipfile.BadZipFile:
            try:
                archive = rarfile.RarFile(self.zipfile)
            except (rarfile.BadRarFile, rarfile.NotRarFile) as e:
                raise ValidationError(
                    {'zipfile': str(e)})
        _secret_path = get_secret_path()
        secret_path = f'{settings.MEDIA_ROOT}/{_secret_path}'
        try:
            archive.extractall(secret_path)
        except (rarfile.BadRarFile, zipfile.BadZipFile) as e:
            raise ValidationError({'zipfile': str(e)})

        images = []

        try:
            html_file_path, _root_folder = _validate_and_find_html(secret_path, '', '', '')

            if not html_file_path:
                raise ValidationError({'zipfile': 'Архив должен содержать html файл'})

            _parse_dir(secret_path, images, '', _root_folder.split('/'))

            self._html_file = html_file_path
            self._images = images
            self._secret_path = _secret_path
        except ValidationError as e:
            shutil.rmtree('/'.join(secret_path.split('/')[:-2]), ignore_errors=True)
            raise ValidationError(e)

    def clean(self):
        super().clean()
        if self.html_from_type == self.HTMLFormType.CKEDITOR:
            if not self.html:
                raise ValidationError({'html': 'Это поле не может быть пустым'})
            self.zipfile = None
            return
        if not self.zipfile:
            raise ValidationError({'zipfile': 'Это поле не может быть пустым'})
        prev_instance = self.__class__.objects.get(pk=self.pk) if self.pk else None
        if not self.pk or prev_instance.zipfile != self.zipfile:
            self._parse_and_validate_zipfile()

    class Meta:
        verbose_name = 'Шаблон'
        verbose_name_plural = 'Шаблоны'
