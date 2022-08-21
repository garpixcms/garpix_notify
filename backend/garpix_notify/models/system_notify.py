import json

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models, transaction
from django.db.models import Manager
from django.utils import timezone
from django.utils.module_loading import import_string

from .template import NotifyTemplate
from .choices import TYPE, STATE
from ..mixins.notify_method_mixin import NotifyMethodsMixin
from ..utils import ReceivingUsers
from garpix_notify.exceptions import IsInstanceException, DataTypeException, ArgumentsEmptyException, UsersListIsNone

SystemNotifyMixin = import_string(settings.GARPIX_SYSTEM_NOTIFY_MIXIN)

User = get_user_model()


class SystemNotify(SystemNotifyMixin, NotifyMethodsMixin):
    """
    Системное уведомление
    """
    title = models.CharField('Название', max_length=255, default='', blank=True)
    user: User = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True, on_delete=models.SET_NULL,
                                   related_name='system_notifies', verbose_name='Пользователь (получатель)')

    type = models.IntegerField('Тип', default=TYPE.SYSTEM, choices=TYPE.CHOICES, blank=True)
    state = models.IntegerField('Состояние', choices=STATE.CHOICES, default=STATE.WAIT)
    event = models.IntegerField('Событие', choices=settings.CHOICES_NOTIFY_EVENT, blank=True, null=True)

    room_name = models.CharField('Название комнаты', max_length=255, null=True, blank=True)
    data_json = models.TextField('Данные JSON', blank=True, null=True)

    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    sent_at = models.DateTimeField('Дата отправки', blank=True, null=True)

    objects = Manager()

    def __str__(self):
        return self.title if self.title and self.title != '' else f'{self.user} - {self.room_name}'

    @staticmethod
    def send(data_json: dict, user: User = None, event: int = None, room_name: str = None,  # noqa: C901
             title: str = None, templates: list = None, **kwargs):

        if user is None and event is None and templates is None:
            raise ArgumentsEmptyException

        if not isinstance(data_json, dict):
            raise DataTypeException(data_json, 'dict')

        if user and not isinstance(user, User):
            raise IsInstanceException

        if templates and not isinstance(templates, list):
            raise DataTypeException('templates', 'list')

        system_notify_user_list: list = []
        notify_json: dict = data_json

        if event and templates is None:
            templates = list(
                NotifyTemplate.objects
                .filter(event=event, is_active=True, type=TYPE.SYSTEM)
                .values_list('id', flat=True)
            )

        if templates:
            templates_instances = (
                NotifyTemplate.objects
                .select_related('user')
                .prefetch_related('user_lists')
                .filter(id__in=templates, is_active=True, type=TYPE.SYSTEM)
            )
            if templates_instances.exists():
                for template in templates_instances:
                    if template.user:
                        system_notify_user_list.append(template.user)
                    notify_json: dict = eval(template.text)

                    if not isinstance(notify_json, dict):
                        raise DataTypeException(notify_json, 'dict')

                    if template.user_lists.exists():
                        notify_users_list = template.user_lists.all()
                        notify_users_list: list = ReceivingUsers.run_receiving_users(notify_users_list, 'user')
                        system_notify_user_list.extend([
                            user for user in notify_users_list if user
                        ])

        if event:
            notify_json['event_id'] = event

        if user:
            system_notify_user_list.append(user)

        if not system_notify_user_list:
            raise UsersListIsNone

        for notify_user in system_notify_user_list:

            user_pk: int = notify_user.pk
            notify_json['user'] = user_pk
            data_json = json.dumps(notify_json)

            notify_room_name = f'room_{user_pk}' if not room_name else room_name
            notify_title = f'{notify_user} - {notify_room_name}' if not title else title

            instance = SystemNotify.objects.create(
                title=notify_title,
                user=notify_user,
                event=event,
                room_name=notify_room_name,
                data_json=data_json,
                **kwargs
            )

            if instance:
                transaction.on_commit(lambda: instance.send_main_system_notifications())

    def send_main_system_notifications(self):
        try:
            if self.room_name:
                group_name = self.room_name
            else:
                group_name = f'room_{self.user.id}'
            async_to_sync(get_channel_layer().group_send)(
                group_name,
                {
                    'id': self.id,
                    'type': 'system',
                    'event': self.event,
                    'data_json': self.data_json,
                }
            )
            self.state = STATE.DELIVERED
            self.sent_at = timezone.now()
        except Exception as e:
            self.state = STATE.REJECTED
            self.to_log(str(e))
        self.save()

    class Meta:
        verbose_name = 'Ситемное уведомление'
        verbose_name_plural = 'Системные уведомления'
