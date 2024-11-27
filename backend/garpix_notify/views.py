import json
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import action
from rest_framework.response import Response
from viberbot import Api, BotConfiguration
from viberbot.api.messages import TextMessage
from .models.config import NotifyConfig
from django.contrib.auth import get_user_model
from django.urls import reverse
from garpix_notify.models import SystemNotify
from garpix_notify.models.choices import TYPE, STATE
from rest_framework.mixins import ListModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet

from .serializers import SystemNotifySerializer, ReadSystemNotifySerializer

User = get_user_model()


# # установка вебхука
def send_webhook(request):
    config = NotifyConfig.get_solo()
    viber = Api(BotConfiguration(
        name=config.viber_bot_name,
        avatar='',
        auth_token=config.viber_api_key
    ))
    current_host = request.META['HTTP_HOST']
    viber.set_webhook(url=f'https://{current_host}' + reverse('viber_check_webhook'),
                      webhook_events=['unsubscribed', 'conversation_started', 'message', 'seen', 'delivered'])


# проверка ивентов
@csrf_exempt
def viber_check_webhook(request):
    if request.method == "POST":
        response = json.loads(request.body.decode('utf-8'))  # получение колбэка
        if response['event'] == 'conversation_started':
            conversation(response)
        if response['event'] == 'subscribed':
            subscribed_event(response)
        if response['event'] == 'message':
            add_viber_user(response)
        if response['event'] == 'webhook':
            return HttpResponse(status=200)
        return HttpResponse(status=200)  # всегда возвращает 200


# отправка приветственного сообщения
def conversation(response):
    config = NotifyConfig.get_solo()
    viber = Api(BotConfiguration(
        name=config.viber_bot_name,
        avatar='',
        auth_token=config.viber_api_key
    ))
    id_user = response['user']['id']
    user_name = response['user']['name']
    if response['subscribed'] == 'false':
        viber.send_messages(to=id_user, messages=[
            TextMessage(text=f'Привет, {user_name}, {config.viber_welcome_text}')
        ])


# доступ к получению сообщений от бота по viber_secret_key
def add_viber_user(response):
    config = NotifyConfig.get_solo()
    viber = Api(BotConfiguration(
        name=config.viber_bot_name,
        avatar='',
        auth_token=config.viber_api_key
    ))
    secret_key = response['message']['text']  # из ответа вайбера берет данные о юзере
    viber_user_id = response['sender']['id']
    viber_user_name = response['sender']['name']
    viber_user = User.objects.filter(viber_secret_key=secret_key).first()  # ищем юзера с верным сикрет кеем
    if viber_user is not None and viber_user.viber_secret_key == secret_key:
        viber_user.viber_chat_id = viber_user_id
        viber_user.save()
        viber.send_messages(to=viber_user_id, messages=[
            TextMessage(text=f'{viber_user_name}, {config.viber_success_added_text}')])
    else:
        viber.send_messages(to=viber_user_id,
                            messages=[TextMessage(text=f'{viber_user_name}, {config.viber_failed_added_text}')])


# ответ на подписку
def subscribed_event(response):
    config = NotifyConfig.get_solo()
    viber = Api(BotConfiguration(
        name=config.viber_bot_name,
        avatar='',
        auth_token=config.viber_api_key
    ))
    id_user = response['user']['id']
    user_name = response['user']['name']
    viber.send_messages(to=id_user, messages=[
        TextMessage(text=f'{user_name},  {config.viber_text_for_new_sub}')
    ])


class SystemNotifyViewSet(ListModelMixin, GenericViewSet):
    permission_classes = [IsAuthenticated]
    filterset_fields = ('type', 'event', 'room_name', 'is_read')
    serializer_class = SystemNotifySerializer

    def get_serializer_class(self):
        if self.action == 'read':
            return ReadSystemNotifySerializer
        if self.action == 'read_all':
            return None
        return SystemNotifySerializer

    def get_queryset(self):
        return SystemNotify.objects.filter(user=self.request.user, type=TYPE.SYSTEM, state=STATE.DELIVERED).order_by(
            '-pk')

    @action(methods=['post'], detail=False)
    def read(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        SystemNotify.read_notifications(serializer.data['ids'])
        return Response({"result": True})

    @action(methods=['post'], detail=False)
    def read_all(self, request, *args, **kwargs):
        SystemNotify.read_notifications(self.get_queryset().values_list('id', flat=True))
        return Response({"result": True})
