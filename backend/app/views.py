from django.shortcuts import render
from garpix_notify.models import Notify
from django.conf import settings


def example_send_notify(request):
    Notify.send(settings.EXAMPLE_EVENT_1, {
        'confirmation_code': 'abcdef12345',
    }, email='aleksey@garpix.com')
    return render(request, 'example.html')
