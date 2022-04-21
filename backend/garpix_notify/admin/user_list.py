from django.contrib import admin
from ..models.user_list import NotifyUserList
from ..models.user_list_participant import NotifyUserListParticipant
from .mainadmin import MainAdmin


class NotifyUserListParticipantInline(admin.TabularInline):
    model = NotifyUserListParticipant
    raw_id_fields = ('user', )
    fields = ('user', 'email')


@admin.register(NotifyUserList)
class NotifyUserListAdmin(MainAdmin):
    list_display = ('title',)
    inlines = [
        NotifyUserListParticipantInline
    ]
    readonly_fields = ('created_at',)
    search_fields = ('title',)
