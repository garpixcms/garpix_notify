from django.db import models
from ..utils import get_file_path


class NotifyFile(models.Model):
    file = models.FileField(upload_to=get_file_path, max_length=1000, verbose_name='Файл')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    def __str__(self):
        return str(self.file.url) if self.file else '-'

    class Meta:
        verbose_name = 'Файл'
        verbose_name_plural = 'Файлы'
