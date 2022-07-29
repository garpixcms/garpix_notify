from django.contrib import admin

from ..models.system_notify import SystemNotify
from .system_log import SystemNotifyErrorLogInline


@admin.register(SystemNotify)
class SystemNotifyAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'type', 'event', 'user', 'get_format_state', 'created_at', 'sent_at')
    readonly_fields = ('created_at', 'type')
    list_filter = ('event', 'state')
    search_fields = ('title', 'user__username')
    raw_id_fields = ('user',)
    inlines = [SystemNotifyErrorLogInline]
