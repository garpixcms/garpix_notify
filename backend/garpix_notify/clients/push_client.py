import json

from django.conf import settings
from django.utils.timezone import now
from django.db import DatabaseError, ProgrammingError

from garpix_notify.models.config import NotifyConfig
from garpix_notify.models.fcm import NotifyDevice
from garpix_notify.models.choices import STATE

# fcm-django 2.x использует firebase-admin, 0.3.x — pyfcm
try:
    from firebase_admin.messaging import Message, Notification
    FCM_DJANGO_V2 = True
except ImportError:
    FCM_DJANGO_V2 = False


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

            if FCM_DJANGO_V2:
                # fcm-django 2.x: firebase-admin API
                data_json = {k: str(v) for k, v in data_json.items()}
                message = Message(
                    notification=Notification(
                        title=self.notify.subject or '',
                        body=self.notify.text or '',
                    ),
                    data=data_json,
                )
                devices.send_message(message)
            else:
                # fcm-django 0.3.x: pyfcm API
                devices.send_message(
                    title=self.notify.subject or '',
                    body=self.notify.text or '',
                    data=data_json,
                )
            self.notify.state = STATE.DELIVERED
            self.notify.sent_at = now()
        except Exception as e:
            self.notify.state = STATE.REJECTED
            self.notify.to_log(str(e))

    @classmethod
    def send_push(cls, notify):
        cls(notify).__send_push_client()
