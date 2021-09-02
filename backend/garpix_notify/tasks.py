from django.utils import timezone
from app.celery import app as celery_app
from .models.choices import STATE
from .models.config import NotifyConfig
from .models.notify import Notify


@celery_app.task
def send_notifications():
    notifies = Notify.objects.filter(state__in=[STATE.WAIT])

    for notify in notifies.iterator():
        if notify.state == STATE.WAIT:
            if notify.send_at is None:
                notify._send()
            else:
                if timezone.now() > notify.send_at:
                    notify._send()
    return


celery_app.conf.beat_schedule.update({
    'periodic_task': {
        'task': 'garpix_notify.tasks.send_notifications',
        'schedule': NotifyConfig.get_solo().periodic,
    },
})
celery_app.conf.timezone = 'UTC'

# celery_app.add_periodic_task(NotifyConfig.get_solo().periodic, send_notifications.s(), name='periodic_task') #2 способ
