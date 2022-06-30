import requests
from django.conf import settings
from django.utils.timezone import now

from garpix_notify.models.config import NotifyConfig
from garpix_notify.models.choices import STATE
from .operators_data import url_dict_call, operator_call, response_check

try:
    config = NotifyConfig.get_solo()
    IS_CALL_ENABLED = config.is_call_enabled
    CALL_URL_TYPE = config.call_url_type
except Exception:
    IS_CALL_ENABLED = True
    CALL_URL_TYPE = getattr(settings, 'CALL_URL_TYPE', 0)


def value_checker(response_dict):
    value = None
    if CALL_URL_TYPE in [NotifyConfig.CALL_URL.SMSRU_CALL_ID, NotifyConfig.CALL_URL.SMSRU_CALL_API_ID]:
        if response_dict['status'] == 'OK':
            value = "OK"
        else:
            value = "BAD"

    elif CALL_URL_TYPE == NotifyConfig.CALL_URL.SMSCENTRE_ID:
        if response_dict['error']:
            value = "BAD"
        else:
            value = "OK"

    elif CALL_URL_TYPE == NotifyConfig.CALL_URL.UCALLER_ID:
        if response_dict['status']:
            value = "OK"
        else:
            value = "BAD"
    return value


class CallClient:

    def send_call_code(self):  # noqa
        if not IS_CALL_ENABLED:
            self.state = STATE.DISABLED
            return
        phone = f'{self.phone}'

        try:
            url = url_dict_call[CALL_URL_TYPE].format(**operator_call[CALL_URL_TYPE], to=phone)
            response_url = requests.get(url)
            response_dict = response_url.json()
            value = value_checker(response_dict)

            response = response_check(response=response_dict, operator_type=CALL_URL_TYPE, status=value)

            self.save_to_log(response=response, value=value)
        except Exception as e:
            self.state = STATE.REJECTED
            self.to_log(str(e))

    def save_to_log(self, response, value):
        if value == "OK":
            self.to_log('Status: {Status}, Code: {Code}, Balance: {Balance}, ID_Call: {ID_Call}'.format(**response))
            self.state = STATE.DELIVERED
            self.sent_at = now()
        elif value == "BAD":
            self.to_log('Status: {Status}, Status_code: {Status_code}, Status_text: {Status_text}'.format(**response))
            self.state = STATE.REJECTED
        else:
            return None

    def direct_call(self, response, value):
        if value == "OK":
            return '{Code}'.format(**response)
        else:
            return None

    @staticmethod
    def call(phone, user=None, url=None, **kwargs):
        if user is not None:
            phone = user.phone if user.phone else phone
        # Для некоторых операторов из представленного списка, мы можем сгенерировать код на нашей стороне
        # Для этого можем передать в функцию кастомную ссылку и дополнительные параметры
        if url is not None:
            url = url
        else:
            url = url_dict_call[CALL_URL_TYPE]
        main_url = url.format(**operator_call[CALL_URL_TYPE], to=phone, **kwargs)
        response_url = requests.get(main_url)
        response_dict = response_url.json()
        value = value_checker(response_dict)

        response = response_check(response=response_dict, operator_type=CALL_URL_TYPE, status=value)
        if value == "OK":
            return '{Code}'.format(**response)
        else:
            return None
