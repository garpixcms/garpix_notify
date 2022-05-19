import datetime

from django.shortcuts import render
from garpix_notify.models import Notify
from django.conf import settings

#Перед началом создайте шаблон для регистрации


def example_send_notify(request):
    Notify.send(settings.REGISTRATION_EVENT, {
        'confirmation_code': 'abcdef12345',
        'message': 'Привет, тут твое сообщение'
    }, email='example@garpix.com', send_at=(datetime.datetime.now() + datetime.timedelta(days=1))
                )
    return render(request, 'example.html')
