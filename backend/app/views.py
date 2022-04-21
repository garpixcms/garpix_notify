from django.shortcuts import render
from garpix_notify.models import Notify
from django.conf import settings

from garpix_notify.models import NotifyCategory

category = NotifyCategory.objects.all().first()


def example_send_notify(request):
    Notify.send(settings.EXAMPLE_EVENT_1, {
        'confirmation_code': 'abcdef12345',
    }, email='aleksey@garpix.com', category='test12'
                )
    return render(request, 'example.html')
