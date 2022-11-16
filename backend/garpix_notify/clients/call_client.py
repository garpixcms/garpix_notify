import requests
import enum
from django.conf import settings
from django.utils.timezone import now

from garpix_notify.models.config import NotifyConfig
from garpix_notify.models.choices import STATE, CALL_URL
from garpix_notify.utils.send_data import SendDataService


class CallClient:

    class ChoiceValue(enum.Enum):
        OK = 0
        BAD = 1

    def __init__(self, notify):
        self.notify = notify
        try:
            self.config = NotifyConfig.get_solo()
            self.IS_CALL_ENABLED = self.config.is_call_enabled
            self.CALL_URL_TYPE = self.config.call_url_type
        except Exception:
            self.IS_CALL_ENABLED = getattr(settings, 'IS_CALL_ENABLED', True)
            self.CALL_URL_TYPE = getattr(settings, 'CALL_URL_TYPE', 0)

    def _value_checker(self, response_dict):
        value = None
        if self.CALL_URL_TYPE in [CALL_URL.SMSRU_CALL_ID, CALL_URL.SMSRU_CALL_API_ID]:
            if response_dict['status'] == "OK":
                value = self.ChoiceValue.OK.value
            else:
                value = self.ChoiceValue.BAD.value

        elif self.CALL_URL_TYPE == CALL_URL.SMSCENTRE_ID:
            if response_dict['error']:
                value = self.ChoiceValue.BAD.value
            else:
                value = self.ChoiceValue.OK.value

        elif self.CALL_URL_TYPE == CALL_URL.UCALLER_ID:
            if response_dict['status']:
                value = self.ChoiceValue.OK.value
            else:
                value = self.ChoiceValue.BAD.value
        return value

    def __send_call_code(self):  # noqa
        if not self.IS_CALL_ENABLED:
            self.notify.state = STATE.DISABLED
            self.notify.to_log('Not sent (sending is prohibited by settings)')
            return

        phone = f'{self.notify.phone}'

        send_data_service = SendDataService()

        try:
            url = send_data_service.url_dict_call[self.CALL_URL_TYPE].format(**send_data_service.operator_call[self.CALL_URL_TYPE], to=phone)
            response_url = requests.get(url)
            response_dict = response_url.json()
            value = self._value_checker(response_dict)

            response = send_data_service.response_check(response=response_dict, operator_type=self.CALL_URL_TYPE, status=value)

            self.__save_to_log(response=response, value=value)
        except Exception as e:
            self.notify.state = STATE.REJECTED
            self.notify.to_log(str(e))

    def __save_to_log(self, response, value):
        if value == self.ChoiceValue.OK.value:
            self.notify.to_log(
                'Status: {Status}, Code: {Code}, Balance: {Balance}, ID_Call: {ID_Call}'.format(**response))
            self.notify.state = STATE.DELIVERED
            self.notify.sent_at = now()
        elif value == self.ChoiceValue.BAD.value:
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
        return cls(notify=None).CALL_URL_TYPE

    @classmethod
    def send_call(cls, notify):
        cls(notify).__send_call_code()
