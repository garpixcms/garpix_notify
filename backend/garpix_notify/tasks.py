from django.utils import timezone
from app.celery import app as celery_app
from .models import NotifyConfig
from .models.choices import STATE, TYPE
from .models.notify import Notify


def iter_notify(notifies):
    for notify in notifies.iterator():
        if notify.state == STATE.WAIT:
            if notify.send_at is None:
                notify._send()
            else:
                if timezone.now() > notify.send_at:
                    notify._send()


@celery_app.task
def send_email_notifications(**kwargs):
    if kwargs:
        notifies = Notify.objects.filter(state__in=[STATE.WAIT], type=TYPE.EMAIL, category__title=kwargs["category"])
    else:
        notifies = Notify.objects.filter(state__in=[STATE.WAIT], type=TYPE.EMAIL)
    iter_notify(notifies)
    return


@celery_app.task
def send_sms_notifications(**kwargs):
    if kwargs:
        notifies = Notify.objects.filter(state__in=[STATE.WAIT], type=TYPE.SMS, category__title=kwargs["category"])
    else:
        notifies = Notify.objects.filter(state__in=[STATE.WAIT], type=TYPE.SMS)
    iter_notify(notifies)
    return


@celery_app.task
def send_push_notifications(**kwargs):
    if kwargs:
        notifies = Notify.objects.filter(state__in=[STATE.WAIT], type=TYPE.PUSH, category__title=kwargs["category"])
    else:
        notifies = Notify.objects.filter(state__in=[STATE.WAIT], type=TYPE.PUSH)
    iter_notify(notifies)
    return


@celery_app.task
def send_telegram_notifications(**kwargs):
    if kwargs:
        notifies = Notify.objects.filter(state__in=[STATE.WAIT], type=TYPE.TELEGRAM, category__title=kwargs["category"])
    else:
        notifies = Notify.objects.filter(state__in=[STATE.WAIT], type=TYPE.TELEGRAM)
    iter_notify(notifies)
    return


@celery_app.task
def send_viber_notifications(**kwargs):
    if kwargs:
        notifies = Notify.objects.filter(state__in=[STATE.WAIT], type=TYPE.VIBER, category__title=kwargs["category"])
    else:
        notifies = Notify.objects.filter(state__in=[STATE.WAIT], type=TYPE.VIBER)
    iter_notify(notifies)
    return


@celery_app.task
def send_system_notifications(**kwargs):
    if kwargs:
        notifies = Notify.objects.filter(state__in=[STATE.WAIT], type=TYPE.SYSTEM, category__title=kwargs["category"])
    else:
        notifies = Notify.objects.filter(state__in=[STATE.WAIT], type=TYPE.SYSTEM)
    iter_notify(notifies)
    return


@celery_app.task
def send_notifications(**kwargs):
    if kwargs:
        notifies = Notify.objects.filter(state__in=[STATE.WAIT], category__title=kwargs["category"])
    else:
        notifies = Notify.objects.filter(state__in=[STATE.WAIT])
    iter_notify(notifies)
    return


celery_app.conf.beat_schedule.update({
    'periodic_task': {
        'task': 'garpix_notify.tasks.send_notifications',
        'schedule': NotifyConfig.get_solo().periodic,
    },
})

celery_app.conf.timezone = 'UTC'
