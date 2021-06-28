from django.contrib import admin
from ..models.file import NotifyFile


@admin.register(NotifyFile)
class NotifyFileAdmin(admin.ModelAdmin):
    list_display = ('file', 'created_at')
    readonly_fields = ('created_at',)
