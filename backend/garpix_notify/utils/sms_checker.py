import requests
from django.conf import settings
from django.utils.timezone import now

from garpix_notify.models.config import NotifyConfig
from garpix_notify.models.choices import STATE
from garpix_notify.utils.receiving import receiving_users
from .operators_data import url_dict_sms, operator_sms

try:
    config = NotifyConfig.get_solo()
    IS_SMS_ENABLED = config.is_sms_enabled
    SMS_URL_TYPE = config.sms_url_type
except Exception:
    IS_SMS_ENABLED = True
    SMS_URL_TYPE = getattr(settings, 'SMS_URL_TYPE', 0)


class SMSClient:

    def send_sms(self):  # noqa

        if not IS_SMS_ENABLED:
            self.state = STATE.DISABLED
            return
        try:
            users_list = self.users_list.all()
            if users_list.count() == 0:
                phones = self.phone
            else:
                phones = receiving_users(users_list, value='phone')
                phones = ','.join(phones)
            msg = str(self.text.replace(' ', '+'))
            url = url_dict_sms[SMS_URL_TYPE].format(**operator_sms[SMS_URL_TYPE], to=phones, text=msg)
            response = requests.get(url)
            response_dict = response.json()
            try:
                if SMS_URL_TYPE == NotifyConfig.SMS_URL.SMSRU_ID:
                    if response_dict['status'] == 'OK':
                        self.to_log(
                            f"Статус основного запроса: {response_dict['status']}, Код статуса: {response_dict['status_code']}, Баланс: {response_dict['balance']}")
                        for key in response_dict['sms']:
                            if response_dict['sms'][key]['status'] == 'ERROR':
                                self.to_log(
                                    f"Ошибка у абонента: Номер: {key}, Статус: {response_dict['sms'][key]['status']}, Код статуса: {response_dict['sms'][key]['status_code']}, Описание: {response_dict['sms'][key]['status_text']}")
                        self.state = STATE.DELIVERED
                        self.sent_at = now()
                    else:
                        self.to_log(
                            f"Статус: {response_dict['status']}, Код статуса: {response_dict['status_code']}, "
                            f"Описание ошибки: {response_dict['status_text']}")
                        self.state = STATE.REJECTED
                elif SMS_URL_TYPE == NotifyConfig.SMS_URL.WEBSZK_ID:
                    try:
                        int(response.text)
                        self.state = STATE.DELIVERED
                        self.sent_at = now()
                    except Exception:
                        self.state = STATE.REJECTED
                elif SMS_URL_TYPE == NotifyConfig.SMS_URL.IQSMS_ID:
                    if response_dict['status'] == 'ok':
                        self.to_log(
                            f"Статус: {response_dict['status']}, Код статуса: {response_dict['code']}, Описание: {response_dict['description']}")
                        self.state = STATE.DELIVERED
                        self.sent_at = now()
                    else:
                        self.to_log(
                            f"Статус: {response_dict['status']}, Код статуса: {response_dict['code']}, "
                            f"Описание ошибки: {response_dict['description']}")
                        self.state = STATE.REJECTED
                elif SMS_URL_TYPE == NotifyConfig.SMS_URL.INFOSMS_ID:
                    self.state = STATE.DELIVERED
                    self.sent_at = now()
                elif SMS_URL_TYPE == NotifyConfig.SMS_URL.SMSCENTRE_ID:
                    self.state = STATE.DELIVERED
                    self.sent_at = now()
                elif SMS_URL_TYPE == NotifyConfig.SMS_URL.SMS_SENDING_ID:
                    if response_dict['code'] == 1:
                        self.to_log(
                            f"Статус: {response_dict['code']}, Описание: {response_dict['descr']}")
                        self.state = STATE.DELIVERED
                        self.sent_at = now()
                    else:
                        self.to_log(
                            f"Статус: {response_dict['code']}, Описание ошибки: {response_dict['descr']}")
                        self.state = STATE.REJECTED
                elif SMS_URL_TYPE == NotifyConfig.SMS_URL.SMS_PROSTO_ID:
                    if response_dict['response']['msg']['err_code'] == 0:
                        self.to_log(
                            f"Статус: {response_dict['response']['msg']['err_code']}, Описание: {response_dict['response']['msg']['text']}")
                        self.state = STATE.DELIVERED
                        self.sent_at = now()
                    else:
                        self.to_log(
                            f"Статус: {response_dict['response']['msg']['err_code']}, Описание ошибки: {response_dict['response']['msg']['text']}")
                        self.state = STATE.REJECTED
            except Exception as e:
                self.state = STATE.REJECTED
                self.to_log(str(e))

        except Exception as e:  # noqa
            self.state = STATE.REJECTED
            self.to_log(str(e))
