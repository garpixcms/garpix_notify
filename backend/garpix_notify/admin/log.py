from django.contrib import admin
from ..models.log import NotifyErrorLog


class NotifyErrorLogInline(admin.TabularInline):
    model = NotifyErrorLog
    fields = ('created_at', 'error')
    readonly_fields = ('created_at', 'error')
    extra = 0

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
