import requests
from django.conf import settings
from django.utils.timezone import now

from garpix_notify.models.config import NotifyConfig
from garpix_notify.models.choices import STATE
from .operators_data import url_dict, operator

try:
    config = NotifyConfig.get_solo()
    IS_CALL_ENABLED = config.is_call_enabled
    CALL_URL_TYPE = config.call_url_type
    CALL_API_ID = config.call_api_id
    CALL_LOGIN = config.call_login
    CALL_PASSWORD = config.call_password
except Exception:
    IS_CALL_ENABLED = True
    CALL_URL_TYPE = getattr(settings, 'CALL_URL_TYPE', 0)
    CALL_API_ID = getattr(settings, 'CALL_API_ID', 1234567890)
    CALL_LOGIN = getattr(settings, 'CALL_LOGIN', '')
    CALL_PASSWORD = getattr(settings, 'CALL_PASSWORD', '')
    CALL_FROM = getattr(settings, 'CALL_FROM', '')


class CallClient:

    def send_call_code(self):  # noqa
        if not IS_CALL_ENABLED:
            self.state = STATE.DISABLED
            return

        try:
            phone = ''.join(self.phone)
            url = url_dict[CALL_URL_TYPE].join(**operator[CALL_URL_TYPE], to=phone)
            print(url)
            response = requests.get(url)
            response_dict = response.json()
            try:
                if CALL_URL_TYPE == NotifyConfig.CALL_URL.SMSRU_CALL_ID or CALL_URL_TYPE == NotifyConfig.CALL_URL.SMSRU_CALL_API_ID:
                    if response_dict['status'] == 'OK':
                        self.to_log(
                            f"Status: {response_dict['status']}, Code: {response_dict['code']}, "
                            f"Баланс: {response_dict['balance']}, ID Звонка: {response_dict['call_id']}")
                        self.state = STATE.DELIVERED
                        self.sent_at = now()
                    else:
                        self.to_log(
                            f"Статус: {response_dict['status']}, Код статуса: {response_dict['status_code']}, "
                            f"Описание ошибки: {response_dict['status_text']}")
                        self.state = STATE.REJECTED

                elif CALL_URL_TYPE == NotifyConfig.CALL_URL.SMSCENTRE_ID:
                    if response_dict['error']:
                        self.to_log(
                            f"Код статуса: {response_dict['error_code']}, "
                            f"Описание ошибки: {response_dict['error']}")
                        self.state = STATE.REJECTED
                    else:
                        self.to_log(
                            f"ID: {response_dict['id']}, Code: {response_dict['code']}, "
                            f"cnt: {response_dict['cnt']}")
                        self.state = STATE.DELIVERED
                        self.sent_at = now()
                elif CALL_URL_TYPE == NotifyConfig.CALL_URL.UCALLER_ID:
                    if response_dict['status']:
                        self.to_log(
                            f"Status: {response_dict['status']}, Code: {response_dict['code']}, ID: {response_dict['ucaller_id']}, "
                            f"ID_Request: {response_dict['unique_request_id']}, Phone: {response_dict['phone']}")
                        self.state = STATE.DELIVERED
                        self.sent_at = now()
                    else:
                        self.to_log(
                            f"Статус: {response_dict['status']}, Код статуса: {response_dict['code']}, Описание: {response_dict['error']}")
                        self.state = STATE.REJECTED
            except Exception as e:
                self.state = STATE.REJECTED
                self.to_log(str(e))
        except Exception as e:  # noqa
            self.state = STATE.REJECTED
            self.to_log(str(e))
