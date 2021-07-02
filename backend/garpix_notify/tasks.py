from django.utils.timezone import timedelta
from .models.config import NotifyConfig
from .models.notify import Notify
from .models.choices import STATE
from celery.task import periodic_task
from django.utils import timezone


def periodic_decorator():
    config = NotifyConfig.get_solo()
    return periodic_task(run_every=timedelta(seconds=config.periodic))


@periodic_decorator()
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
