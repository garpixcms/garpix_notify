from django.urls import path
from .views import send_webhook, viber_check_webhook

urlpatterns = [
    path('send_webhook', send_webhook, name='send_webhook'),
    path('viber_check_webhook', viber_check_webhook, name='viber_check_webhook'),
]
