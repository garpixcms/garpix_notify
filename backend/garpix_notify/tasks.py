from django.utils import timezone
from app.celery import app as celery_app
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from .models.choices import STATE, TYPE
from .models.config import NotifyConfig
from .models.notify import Notify


@celery_app.task
def send_notifications():
    notifies = Notify.objects.filter(state__in=[STATE.WAIT]).exclude(type=TYPE.SYSTEM)

    for notify in notifies.iterator():
        if notify.state == STATE.WAIT:
            if notify.send_at is None:
                notify._send()
            else:
                if timezone.now() > notify.send_at:
                    notify._send()
    return


@celery_app.task
def send_system_notifications(notify_pk):
    try:
        instance = Notify.objects.get(pk=notify_pk)
        if instance.room_name:
            group_name = instance.room_name
        else:
            group_name = f'room_{instance.user.id}'
        async_to_sync(get_channel_layer().group_send)(
            group_name,
            {
                'type': 'send_notify',
                'event': instance.event,
                'message': instance.html
            }
        )
        instance.state = STATE.DELIVERED
        instance.sent_at = timezone.now()
    except Exception as e:  # noqa
        instance.state = STATE.REJECTED
        instance.to_log(str(e))
    instance.save()
    return


celery_app.conf.beat_schedule.update({
    'periodic_task': {
        'task': 'garpix_notify.tasks.send_notifications',
        'schedule': NotifyConfig.get_solo().periodic,
    },
})
celery_app.conf.timezone = 'UTC'
