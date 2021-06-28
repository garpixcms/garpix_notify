from django.contrib import admin
from ..models.smtp import SMTPAccount


def clear_limits(modeladmin, request, queryset):
    for server in queryset.all():
        server.clear()


clear_limits.short_description = 'Обнулить лимиты'


@admin.register(SMTPAccount)
class SMTPAccountAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'is_worked_now')
    readonly_fields = ('email_hour_used_times', 'email_hour_used_date', 'email_day_used_times', 'email_day_used_date')
    actions = [
        clear_limits
    ]
