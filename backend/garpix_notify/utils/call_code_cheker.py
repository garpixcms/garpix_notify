import requests
from django.conf import settings
from django.utils.timezone import now

from garpix_notify.models.config import NotifyConfig
from garpix_notify.models.choices import STATE
from garpix_notify.utils.receiving import receiving_users

try:
    config = NotifyConfig.get_solo()
    IS_CALL_ENABLED = config.is_call_enabled
    CALL_URL_TYPE = config.call_url_type
    CALL_API_ID = config.call_api_id
    CALL_LOGIN = config.call_login
    CALL_PASSWORD = config.call_password
    CALL_FROM = config.call_from
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
            url = None
            users_list = self.users_list.all()
            if users_list.count() == 0:
                phones = self.phone
            else:
                phones = receiving_users(users_list, value='phone')
                phones = ','.join(phones)
            if CALL_URL_TYPE == NotifyConfig.CALL_URL.SMSRU_CALL_API_ID:
                url = '{url}?phone={to}&api_id={api_id}&json=1'.format(
                    url=NotifyConfig.CALL_URL.SMSRU_CALL_URL,
                    api_id=CALL_API_ID,
                    to=phones,
                )
            if CALL_URL_TYPE == NotifyConfig.CALL_URL.SMSRU_CALL_ID:
                url = '{url}?phone={to}&login={login}&password={password}&json=1'.format(
                    url=NotifyConfig.CALL_URL.SMSRU_CALL_URL,
                    login=CALL_LOGIN,
                    password=CALL_PASSWORD,
                    to=phones,
                )
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
            except Exception as e:
                self.state = STATE.REJECTED
                self.to_log(str(e))

        except Exception as e:  # noqa
            self.state = STATE.REJECTED
            self.to_log(str(e))
