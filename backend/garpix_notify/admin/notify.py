from django.contrib import admin, messages

from ..models import NotifyTemplate
from ..models.notify import Notify
from .log import NotifyErrorLogInline


class FileInline(admin.TabularInline):
    model = Notify.files.through
    verbose_name = 'Файл'
    verbose_name_plural = 'Файлы'
    raw_id_fields = ('notifyfile',)
    extra = 0


@admin.register(Notify)
class NotifyAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'type', 'event', 'user', 'email', 'phone', 'get_format_state', 'created_at', 'send_at',
                    'sent_at')
    inlines = [
        FileInline,
        NotifyErrorLogInline
    ]
    readonly_fields = ('created_at',)
    exclude = ('files',)
    list_filter = ('event', 'state', 'type', 'category')
    search_fields = ('subject', 'text')
    raw_id_fields = ('user',)
    filter_horizontal = ('users_list', )

    def get_changelist(self, request, **kwargs):
        events_message = NotifyTemplate.get_blank_events_message()
        if events_message:
            self.message_user(request, events_message, level=messages.WARNING)
        return super().get_changelist(request, **kwargs)
