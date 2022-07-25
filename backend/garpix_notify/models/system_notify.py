import json

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models, transaction
from django.db.models.signals import post_save
from django.db.models import Manager
from django.utils.module_loading import import_string
from django.dispatch import receiver

from .template import NotifyTemplate
from .choices import TYPE, STATE
from ..mixins.notify_method_mixin import NotifyMethodsMixin
from ..utils import ReceivingUsers
from garpix_notify.exceptions import IsInstanceException, DataTypeException, ArgumentsEmptyException

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
             title: str = '', **kwargs):

        if user is None and event is None:
            raise ArgumentsEmptyException

        if not isinstance(data_json, dict):
            raise DataTypeException(data_json)

        if user and not isinstance(user, User):
            raise IsInstanceException

        system_notify_user_list: list = []
        notify_json: dict = data_json
        template = None

        if event:
            template = (
                NotifyTemplate.objects
                .select_related('user')
                .prefetch_related('user_lists')
                .prefetch_related('user_lists__user_groups')
                .filter(event=event, is_active=True, type=TYPE.SYSTEM)
                .first()
            )

        if template:
            if template.user:
                system_notify_user_list.append(template.user)
            notify_json: dict = eval(template.text)

            if not isinstance(notify_json, dict):
                raise DataTypeException(notify_json)

            if template.user_lists.exists():
                notify_users_list = template.user_lists.all()
                notify_users_list: list = ReceivingUsers.run_receiving_users(notify_users_list, 'user')
                system_notify_user_list.extend([
                    user for user in notify_users_list if user
                ])

        notify_json['event_id'] = event

        if user:
            system_notify_user_list.append(user)

        for user_notify in system_notify_user_list:
            user_pk: int = user_notify.pk
            notify_json['user'] = user_pk
            room_name: str = room_name if room_name else f'room_{user_pk}'
            data_json = json.dumps(notify_json)
            if title == '':
                title = f'{user_notify} - {room_name}'

            SystemNotify.objects.create(
                title=title,
                user=user_notify,
                event=event,
                room_name=room_name,
                data_json=data_json,
                **kwargs
            )

    class Meta:
        verbose_name = 'Ситемное уведомление'
        verbose_name_plural = 'Системные уведомления'


@receiver(post_save, sender=SystemNotify)
def system_post_save(sender, instance, created, **kwargs):
    from garpix_notify.tasks.tasks import send_main_system_notifications
    if created:
        transaction.on_commit(lambda: send_main_system_notifications.delay(instance.pk))
