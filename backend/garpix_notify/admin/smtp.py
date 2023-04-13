from django.contrib import admin, messages
from django.http import HttpResponseRedirect

from ..models.smtp import SMTPAccount


def clear_limits(modeladmin, request, queryset):
    for server in queryset.all():
        server.clear()


clear_limits.short_description = 'Обнулить лимиты'


@admin.register(SMTPAccount)
class SMTPAccountAdmin(admin.ModelAdmin):
    change_form_template = "test_smtp_account.html"
    list_display = ('__str__', 'is_worked_now')
    readonly_fields = ('email_hour_used_times', 'email_hour_used_date', 'email_day_used_times', 'email_day_used_date')
    actions = [
        clear_limits
    ]

    def response_change(self, request, obj):

        if "_test_smtp" in request.POST:
            try:
                obj.test_account()
                self.message_user(request, 'Успешно', level=messages.SUCCESS)
            except Exception as e:
                self.message_user(request, str(e), level=messages.ERROR)
            return HttpResponseRedirect(".")

        return super().response_change(request, obj)
