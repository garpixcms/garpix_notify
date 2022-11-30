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
        'html',
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
                'category': obj.category
            },
            TYPE.EMAIL: {
                'subject': obj.render_subject(template.subject),
                'text': obj.render_text(context),
                'html': obj.render_html(context),
                'user': user,
                'email': template.email,
                'type': TYPE.EMAIL,
                'category': obj.category
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
