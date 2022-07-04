import requests
from django.conf import settings
from django.utils.timezone import now

from garpix_notify.models.config import NotifyConfig
from garpix_notify.models.choices import STATE, CALL_URL
from garpix_notify.utils.send_data import url_dict_call, operator_call, response_check

try:
    config = NotifyConfig.get_solo()
    IS_CALL_ENABLED = config.is_call_enabled
    CALL_URL_TYPE = config.call_url_type
except Exception:
    IS_CALL_ENABLED = True
    CALL_URL_TYPE = getattr(settings, 'CALL_URL_TYPE', 0)


class CallClient:

    def __init__(self, notify):
        self.notify = notify

    CALL_URL_TYPE = CALL_URL_TYPE

    def _value_checker(self, response_dict):
        value = None
        if self.CALL_URL_TYPE in [CALL_URL.SMSRU_CALL_ID, CALL_URL.SMSRU_CALL_API_ID]:
            if response_dict['status'] == 'OK':
                value = "OK"
            else:
                value = "BAD"

        elif self.CALL_URL_TYPE == CALL_URL.SMSCENTRE_ID:
            if response_dict['error']:
                value = "BAD"
            else:
                value = "OK"

        elif self.CALL_URL_TYPE == CALL_URL.UCALLER_ID:
            if response_dict['status']:
                value = "OK"
            else:
                value = "BAD"
        return value

    def __send_call_code(self):  # noqa
        if not IS_CALL_ENABLED:
            self.notify.state = STATE.DISABLED
            return
        phone = f'{self.notify.phone}'

        try:
            url = url_dict_call[self.CALL_URL_TYPE].format(**operator_call[self.CALL_URL_TYPE], to=phone)
            response_url = requests.get(url)
            response_dict = response_url.json()
            value = self._value_checker(response_dict)

            response = response_check(response=response_dict, operator_type=self.CALL_URL_TYPE, status=value)

            self.notify.save_to_log(response=response, value=value)
        except Exception as e:
            self.notify.state = STATE.REJECTED
            self.notify.to_log(str(e))

    def save_to_log(self, response, value):
        if value == "OK":
            self.notify.to_log(
                'Status: {Status}, Code: {Code}, Balance: {Balance}, ID_Call: {ID_Call}'.format(**response))
            self.notify.state = STATE.DELIVERED
            self.notify.sent_at = now()
        elif value == "BAD":
            self.notify.to_log(
                'Status: {Status}, Status_code: {Status_code}, Status_text: {Status_text}'.format(**response))
            self.notify.state = STATE.REJECTED
        else:
            return None

    @classmethod
    def get_value_checker(cls, response_dict):
        return cls(notify=None)._value_checker(response_dict)

    @classmethod
    def get_url_type(cls):
        return cls.CALL_URL_TYPE

    @classmethod
    def send_call(cls, notify):
        cls(notify).__send_call_code()
