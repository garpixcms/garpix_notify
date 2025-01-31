import re

from django.conf import settings
from django.contrib import admin, messages

from ..models import SystemNotify, Notify
from ..models.choices import TYPE
from ..models.template import NotifyTemplate
from django.http import HttpResponseRedirect


@admin.register(NotifyTemplate)
class NotifyTemplateAdmin(admin.ModelAdmin):
    change_form_template = "send_notify.html"
    fields = (
        'title',
        'is_active',
        'subject',
        'is_delete_after',
        'get_context_description',
        'text',
        'html_from_type',
        'html',
        'zipfile',
        'user',
        'email',
        'phone',
        'telegram_chat_id',
        'viber_chat_id',
        'type',
        'category',
        'event',
        'user_lists',
        'send_at',
    )
    readonly_fields = (
        'get_context_description',
        'get_event_description',
    )
    list_display = ('title', 'is_active', 'type', 'category', 'event', 'user', 'email', 'phone', 'send_at')
    list_filter = ('type', 'category', 'event', 'is_active')
    actions = ['create_mailing', ]
    filter_horizontal = ('user_lists',)
    raw_id_fields = ('user',)

    def create_mailing(self, request, queryset):
        count = Notify.send(event=None, context={}, notify_templates=queryset)
        self.message_user(request, 'Рассылка создана, кол-во сообщений: {}'.format(count))

    create_mailing.short_description = "Сделать рассылку"

    def response_change(self, request, obj):
        template = obj
        context = obj.get_test_data()
        user = obj.user if obj.user else request.user

        type_test_message = {
            TYPE.SMS: {
                'subject': obj.render_subject(template.subject),
                'text': obj.render_text(context),
                'user': user,
                'phone': template.phone,
                'type': TYPE.SMS,
                'category': obj.category,
                'is_delete_after': template.is_delete_after
            },
            TYPE.EMAIL: {
                'subject': obj.render_subject(template.subject),
                'text': obj.render_text(context),
                'html': obj.render_html(context),
                'user': user,
                'email': template.email,
                'type': TYPE.EMAIL,
                'category': obj.category,
                'is_delete_after': template.is_delete_after
            },
            TYPE.PUSH: {
                'subject': obj.render_subject(template.subject),
                'text': obj.render_text(context),
                'user': user,
                'type': TYPE.PUSH,
                'category': obj.category
            },
            TYPE.CALL: {
                'subject': obj.render_subject(template.subject),
                'text': obj.render_text(context),
                'user': user,
                'phone': template.phone,
                'type': TYPE.SMS,
                'category': obj.category
            },
        }

        if obj.user_lists and "_send_now" in request.POST:
            instance = Notify.objects.create(**type_test_message.get(obj.type, TYPE.EMAIL))
            instance.start_send()
            self.message_user(request, 'Тестовое уведомление отправлено', level=messages.SUCCESS)
            return HttpResponseRedirect(".")
        elif "_send_now_system" in request.POST:
            instance = SystemNotify.objects.create(
                title=template.subject if template.subject or template.subject != '' else template.title,
                event=template.event,
                user=user,
                data_json=context,
                room_name=f'room_{user.pk}'
            )
            instance.send_notification()
            self.message_user(request, 'Тестовое уведомление отправлено', level=messages.SUCCESS)
            return HttpResponseRedirect(".")

        return super().response_change(request, obj)

    def get_changelist(self, request, **kwargs):
        events_message = NotifyTemplate.get_blank_events_message()
        if events_message:
            self.message_user(request, events_message, level=messages.WARNING)
        return super().get_changelist(request, **kwargs)

    def save_model(self, request, obj, form, change):
        if hasattr(obj, '_html_file'):
            with open(obj._html_file, 'r') as f:
                _html = f.read()
                for img in obj._images:
                    _full_img_url = request.build_absolute_uri(
                        f"{settings.MEDIA_URL}{obj._secret_path}/{img['file_path']}")
                    _html = re.sub(r"src *= *[\"'](\./)*({0})[\"']".format(img['html_path']), f"src='{_full_img_url}'",
                                   _html)
                    _html = re.sub(r"url *\( *[\"'](\./)*({0})[\"'] *\)".format(img['html_path']),
                                   f"url('{_full_img_url}')", _html)
                obj.html = _html
        super().save_model(request, obj, form, change)

    class Media:
        css = {
            'all': ('css/admin/garpix_notify.css',)
        }
        js = ('js/admin/garpix_notify.js',)
