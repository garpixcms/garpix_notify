from django.conf import settings
from django.utils import timezone
from django.utils.module_loading import import_string
from django.db.models import Q
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from garpix_notify.models.choices import STATE, TYPE
from garpix_notify.models.config import NotifyConfig
from garpix_notify.models.notify import Notify


celery_app = import_string(settings.GARPIX_NOTIFY_CELERY_SETTINGS)

try:
    config = NotifyConfig.get_solo()
    PERIODIC_SENDING = config.periodic
except Exception:
    PERIODIC_SENDING = getattr(settings, 'PERIODIC_SENDING', 60)


def get_notifications_to_send():
    return (
        Notify.objects
        .filter(
            Q(state__in=(STATE.WAIT,)) &
            (
                Q(send_at__isnull=True) | Q(send_at__lte=timezone.now())
            )
        )
        .exclude(type=TYPE.SYSTEM)
        .iterator()
    )


@celery_app.task
def send_notifications():
    notifies = get_notifications_to_send()
    for notify in notifies:
        notify.start_send()


@celery_app.task
def send_system_notifications(notify_pk):
    instance = Notify.objects.get(pk=notify_pk)

    try:
        if instance.room_name:
            group_name = instance.room_name
        else:
            group_name = f'room_{instance.user.id}'

        async_to_sync(get_channel_layer().group_send)(
            group_name,
            {
                'id': notify_pk,
                'type': 'send_notify',
                'event': instance.event,
                'message': instance.html,
                'json_data': instance.data_json,
            }
        )

        instance.state = STATE.DELIVERED
        instance.sent_at = timezone.now()
    except Exception as e:  # noqa
        instance.state = STATE.REJECTED
        instance.to_log(str(e))

    instance.save()


celery_app.conf.beat_schedule.update({
    'periodic_task': {
        'task': 'garpix_notify.tasks.tasks.send_notifications',
        'schedule': PERIODIC_SENDING,
    }
})
celery_app.conf.timezone = 'UTC'
