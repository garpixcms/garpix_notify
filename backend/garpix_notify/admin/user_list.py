from django.contrib import admin
from ..models.user_list import NotifyUserList
from ..models.user_list_participant import NotifyUserListParticipant


class NotifyUserListParticipantInline(admin.TabularInline):
    model = NotifyUserListParticipant
    raw_id_fields = ('user', )
    fields = ('user', 'email', 'phone', 'viber_chat_id')


@admin.register(NotifyUserList)
class NotifyUserListAdmin(admin.ModelAdmin):
    list_display = ('title',)
    inlines = [
        NotifyUserListParticipantInline
    ]
    readonly_fields = ('created_at',)
    search_fields = ('title',)
    filter_horizontal = ('user_groups', 'users')
