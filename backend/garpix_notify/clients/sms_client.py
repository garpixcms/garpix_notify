import requests
from django.conf import settings
from django.utils.timezone import now

from garpix_notify.models.config import NotifyConfig
from garpix_notify.models.choices import STATE, SMS_URL
from garpix_notify.utils.receiving import ReceivingUsers
from garpix_notify.utils.send_data import SendDataService


class SMSClient:

    def __init__(self, notify):
        self.notify = notify
        try:
            self.config = NotifyConfig.get_solo()
            self.IS_SMS_ENABLED = self.config.is_sms_enabled
            self.SMS_URL_TYPE = self.config.sms_url_type
        except Exception:
            self.IS_SMS_ENABLED = getattr(settings, 'IS_SMS_ENABLED', True)
            self.SMS_URL_TYPE = getattr(settings, 'SMS_URL_TYPE', 0)

    def __client_sms(self):  # noqa

        if not self.IS_SMS_ENABLED:
            self.notify.state = STATE.DISABLED
            self.notify.to_log('Not sent (sending is prohibited by settings)')
            return

        try:
            send_data_service = SendDataService()
            users_list = self.notify.users_list.all()
            if not users_list.exists():
                phones: str = self.notify.phone
            else:
                phones_list: list = ReceivingUsers.run_receiving_users(users_list, 'phone')
                phones = ','.join(phones_list)
            msg = str(self.notify.text.replace(' ', '+'))
            url = send_data_service.url_dict_sms[self.SMS_URL_TYPE].format(
                **send_data_service.operator_sms[self.SMS_URL_TYPE], to=phones, text=msg)
            response = requests.get(url)
            response_dict = response.json()
            try:
                if self.SMS_URL_TYPE == SMS_URL.SMSRU_ID:
                    if response_dict['status'] == 'OK':
                        self.notify.to_log(
                            f"Статус основного запроса: {response_dict['status']}, Код статуса: \
                            {response_dict['status_code']}, Баланс: {response_dict['balance']}")
                        for key in response_dict['sms']:
                            if response_dict['sms'][key]['status'] == 'ERROR':
                                self.notify.to_log(
                                    f"Ошибка у абонента: Номер: {key}, Статус: {response_dict['sms'][key]['status']}, \
                                    Код статуса: {response_dict['sms'][key]['status_code']}, Описание: \
                                    {response_dict['sms'][key]['status_text']}")
                        self.notify.state = STATE.DELIVERED
                        self.notify.sent_at = now()
                    else:
                        self.notify.to_log(
                            f"Статус: {response_dict['status']}, Код статуса: {response_dict['status_code']}, "
                            f"Описание ошибки: {response_dict['status_text']}")
                        self.notify.state = STATE.REJECTED
                elif self.SMS_URL_TYPE == SMS_URL.WEBSZK_ID:
                    try:
                        int(response.text)
                        self.notify.state = STATE.DELIVERED
                        self.notify.sent_at = now()
                    except Exception as e:
                        self.notify.to_log(str(e))
                        self.notify.state = STATE.REJECTED
                elif self.SMS_URL_TYPE == SMS_URL.IQSMS_ID:
                    if response_dict['status'] == 'ok':
                        self.notify.to_log(
                            f"Статус: {response_dict['status']}, Код статуса: {response_dict['code']}, Описание: \
                            {response_dict['description']}")
                        self.notify.state = STATE.DELIVERED
                        self.notify.sent_at = now()
                    else:
                        self.notify.to_log(
                            f"Статус: {response_dict['status']}, Код статуса: {response_dict['code']}, "
                            f"Описание ошибки: {response_dict['description']}")
                        self.notify.state = STATE.REJECTED
                elif self.SMS_URL_TYPE == SMS_URL.INFOSMS_ID:
                    self.notify.state = STATE.DELIVERED
                    self.notify.sent_at = now()
                elif self.SMS_URL_TYPE == SMS_URL.SMSCENTRE_ID:
                    self.notify.state = STATE.DELIVERED
                    self.notify.sent_at = now()
                elif self.SMS_URL_TYPE == SMS_URL.SMS_SENDING_ID:
                    if response_dict['code'] == 1:
                        self.notify.to_log(
                            f"Статус: {response_dict['code']}, Описание: {response_dict['descr']}")
                        self.notify.state = STATE.DELIVERED
                        self.notify.sent_at = now()
                    else:
                        self.notify.to_log(
                            f"Статус: {response_dict['code']}, Описание ошибки: {response_dict['descr']}")
                        self.notify.state = STATE.REJECTED
                elif self.SMS_URL_TYPE == SMS_URL.SMS_PROSTO_ID:
                    if response_dict['response']['msg']['err_code'] == 0:
                        self.notify.to_log(
                            f"Статус: {response_dict['response']['msg']['err_code']}, Описание: \
                            {response_dict['response']['msg']['text']}")
                        self.notify.state = STATE.DELIVERED
                        self.notify.sent_at = now()
                    else:
                        self.notify.to_log(
                            f"Статус: {response_dict['response']['msg']['err_code']}, Описание ошибки: \
                            {response_dict['response']['msg']['text']}")
                        self.notify.state = STATE.REJECTED
            except Exception as e:
                self.notify.state = STATE.REJECTED
                self.notify.to_log(str(e))

        except Exception as e:  # noqa
            self.notify.state = STATE.REJECTED
            self.notify.to_log(str(e))

    @classmethod
    def send_sms(cls, notify):
        cls(notify).__client_sms()
