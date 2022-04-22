from django.shortcuts import render
from garpix_notify.models import Notify
from django.conf import settings

from garpix_notify.models import NotifyCategory

category = NotifyCategory.objects.all().first()


def example_send_notify(request):
    Notify.send(settings.REGISTRATION_EVENT, {
        'confirmation_code': 'abcdef12345',
        'message': 'Привет, тут твое сообщение'
    }, email='aleksey@garpix.com',
                )
    return render(request, 'example.html')
