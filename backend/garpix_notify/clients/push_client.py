import json

from django.conf import settings
from django.utils.timezone import now

from garpix_notify.models.config import NotifyConfig
from garpix_notify.models.fcm import NotifyDevice
from garpix_notify.models.choices import STATE


class PushClient:
    IS_PUSH_ENABLED = True

    def __init__(self, notify):
        self.notify = notify
        self.__get_config_settings()

    def __get_config_settings(self):
        try:
            self.config = NotifyConfig.get_solo()
            self.IS_PUSH_ENABLED = self.config.is_push_enabled
        except Exception:
            self.IS_PUSH_ENABLED = getattr(settings, 'IS_PUSH_ENABLED', True)

    def __send_push_client(self):

        if not self.IS_PUSH_ENABLED:
            self.notify.state = STATE.DISABLED
            self.notify.to_log('Not sent (sending is prohibited by settings)')
            return

        if self.notify.user is None:
            self.notify.state = STATE.REJECTED
            self.notify.save()
            return

        devices = NotifyDevice.objects.filter(active=True, user=self.notify.user).distinct('device_id')

        data_json = {}
        if self.notify.data_json is not None:
            data_json = json.loads(self.notify.data_json)
        data_json.update({
            'notify_id': self.notify.id,
        })

        try:
            devices.send_message(title=self.notify.subject, body=self.notify.text, data=data_json)
            self.notify.state = STATE.DELIVERED
            self.notify.sent_at = now()
        except Exception as e:  # noqa
            self.notify.state = STATE.REJECTED
            self.notify.to_log(str(e))

    @classmethod
    def send_push(cls, notify):
        cls(notify).__send_push_client()
