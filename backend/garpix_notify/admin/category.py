from django.contrib import admin
from garpix_notify.models.category import NotifyCategory


@admin.register(NotifyCategory)
class NotifyCategoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at')
    readonly_fields = ('created_at',)
