from django.urls import re_path
from . import consumers


websocket_urlpatterns = [
    re_path(r'(?P<user_id>\w+)/$', consumers.NotifyConsumer.as_asgi()),
]
