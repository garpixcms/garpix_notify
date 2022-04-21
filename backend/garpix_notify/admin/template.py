from django.contrib import admin
from ..models.template import NotifyTemplate
from ..models.notify import Notify
from django.http import HttpResponseRedirect
from ..models import NotifyCategory, SMTPAccount
from .mainadmin import MainAdmin


@admin.register(NotifyTemplate)
class NotifyTemplateAdmin(MainAdmin):
    change_form_template = "send_notify.html"
    fields = (
        'title',
        'is_active',
        'subject',
        'get_context_description',
        'text',
        'html',
        'telegram_chat_id',
        'viber_chat_id',
        'type',
        'event',
        'user_lists',
        'send_at',
    )
    readonly_fields = (
        'get_context_description',
        'get_event_description',
    )
    list_display = ('title', 'is_active', 'type', 'event', 'send_at')
    list_filter = ('type', 'event', 'is_active')
    actions = ['create_mailing', ]

    def create_mailing(self, request, queryset):
        count = Notify.send(event=None, context={}, notify_templates=queryset)
        self.message_user(request, 'Рассылка создана, кол-во сообщений: {}'.format(count))
    create_mailing.short_description = "Сделать рассылку"

    def response_change(self, request, obj):
        from ..models.notify import Notify
        if obj.user_lists and "_send_now" in request.POST:

            context = obj.get_test_data()
            template = obj
            category = NotifyCategory.objects.create(
                title=template.title,
                template_choice=template,
            )
            smtp = SMTPAccount.objects.all()
            if smtp is None:
                print('>No smtp-accounts detected!<')
            else:
                smtp = SMTPAccount.objects.first()
                smtp.category = category
                smtp.save()
                print(f'>Changes have been made for {smtp.sender}<')
            instance = Notify.objects.create(
                subject=template.render_subject(template.subject),
                text=template.render_text(context),
                html=template.render_html(context),
                type=template.type,
                category=category
            )
            instance.save()
            instance._send()
            return HttpResponseRedirect(".")
        return super().response_change(request, obj)
