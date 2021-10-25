import json
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer


class NotifyConsumer(WebsocketConsumer):
    def connect(self):
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.room_group_name = f'room_{self.user_id}'
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )
        self.accept()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

    def send_notify(self, event):
        message = event['message']
        self.send(text_data=json.dumps({
            'message': message
        }))
