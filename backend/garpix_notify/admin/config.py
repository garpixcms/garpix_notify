from django.contrib import admin
from solo.admin import SingletonModelAdmin
from ..models.config import NotifyConfig


@admin.register(NotifyConfig)
class NotifyConfigAdmin(SingletonModelAdmin):
    fieldsets = (
        (None, {
            'fields': ('periodic', 'is_email_enabled', 'is_sms_enabled', 'is_push_enabled', 'is_telegram_enabled',
                       'is_viber_enabled')
        }),
        ('Почта', {
            'fields': ('email_max_day_limit', 'email_max_hour_limit')
        }),
        ('СМС', {
            'fields': ('sms_url', 'sms_api_id', 'sms_from')
        }),
        ('Telegram', {
            'fields': ('telegram_api_key',)
        }),
        ('Viber', {
            'fields': ('viber_api_key', 'viber_bot_name', 'viber_success_added_text',
                       'viber_failed_added_text', 'viber_text_for_new_sub', 'viber_welcome_text')
        })
    )
