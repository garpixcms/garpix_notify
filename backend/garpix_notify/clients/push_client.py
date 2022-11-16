import json

from django.conf import settings
from django.utils.timezone import now
from django.db import DatabaseError, ProgrammingError

from garpix_notify.models.config import NotifyConfig
from garpix_notify.models.fcm import NotifyDevice
from garpix_notify.models.choices import STATE


class PushClient:

    def __init__(self, notify):
        self.notify = notify
        try:
            self.config = NotifyConfig.get_solo()
            self.IS_PUSH_ENABLED = self.config.is_push_enabled
        except (DatabaseError, ProgrammingError):
            self.IS_PUSH_ENABLED = getattr(settings, 'IS_PUSH_ENABLED', True)

    def __send_push_client(self):

        if not self.IS_PUSH_ENABLED or self.notify.user is None:
            if self.notify.user is None:
                message = 'No users found'
                self.notify.state = STATE.REJECTED
            else:
                message = 'Not sent (sending is prohibited by settings)'
                self.notify.state = STATE.DISABLED
            self.notify.to_log(message)
            return

        devices = NotifyDevice.objects.filter(active=True, user=self.notify.user).distinct('device_id')
        data_json: dict = {}

        try:
            data_json.update({
                'notify_id': self.notify.id,
                'sound': 'default'
            })

            if self.notify.data_json is not None:
                data_json.update(json.loads(self.notify.data_json))

            devices.send_message(title=self.notify.subject, body=self.notify.text, data=data_json)
            self.notify.state = STATE.DELIVERED
            self.notify.sent_at = now()
        except Exception as e:
            self.notify.state = STATE.REJECTED
            self.notify.to_log(str(e))

    @classmethod
    def send_push(cls, notify):
        cls(notify).__send_push_client()
