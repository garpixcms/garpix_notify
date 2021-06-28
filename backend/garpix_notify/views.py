import json
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from viberbot import Api, BotConfiguration
from viberbot.api.messages import TextMessage
from .models.config import NotifyConfig
from django.contrib.auth import get_user_model
from django.urls import reverse

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
    print(reverse("viber_check_webhook"), 'reverse(viber_check_webhook)')
    viber.set_webhook(url=f'https://{current_host}' + reverse('viber_check_webhook'),
                      webhook_events=['unsubscribed', 'conversation_started', 'message', 'seen', 'delivered'])


# проверка ивентов
@csrf_exempt
def viber_check_webhook(request):
    if request.method == "POST":
        response = json.loads(request.body.decode('utf-8'))  # получение колбэка
        if response['event'] == 'conversation_started':
            print("Приветствую пользователя")
            conversation(response)
        if response['event'] == 'subscribed':
            print("subscribed event")
            subscribed_event(response)
        if response['event'] == 'message':
            print("message event")
            add_viber_user(response)
        if response['event'] == 'webhook':
            print(response)
            print("Webhook успешно установлен")
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
    print(id_user, ' id in conversation')
    if response['subscribed'] == 'false':
        print(response, 'response in conversation')
        viber.send_messages(to=id_user, messages=[
            TextMessage(text=f'Привет, {user_name}, {config.viber_welcome_text}')])


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
        TextMessage(text=f'{user_name},  {config.viber_text_for_new_sub}')])
