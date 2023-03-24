from django.conf import settings
from django.urls import path
from .views import send_webhook, viber_check_webhook, SystemNotifyViewSet
from rest_framework.routers import DefaultRouter

app_name = 'garpix_notify'

router = DefaultRouter()

router.register(f'{settings.API_URL}/garpix_notify/system_notifies', SystemNotifyViewSet, basename='system_notifies')

urlpatterns = [
    path('send_webhook', send_webhook, name='send_webhook'),
    path('viber_check_webhook', viber_check_webhook, name='viber_check_webhook'),
] + router.urls
