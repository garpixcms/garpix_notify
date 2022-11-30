import requests

from typing import Optional, Union
from requests import Response

from django.conf import settings
from django.utils.timezone import now
from django.db import DatabaseError, ProgrammingError

from garpix_notify.models.config import NotifyConfig
from garpix_notify.models.choices import STATE, SMS_URL
from garpix_notify.utils.receiving import ReceivingUsers
from garpix_notify.utils.send_data import SendData


class SMSClient:

    def __init__(self, notify):
        self.notify = notify
        try:
            self.config = NotifyConfig.get_solo()
            self.IS_SMS_ENABLED = self.config.is_sms_enabled
            self.SMS_URL_TYPE = self.config.sms_url_type
        except (DatabaseError, ProgrammingError):
            self.IS_SMS_ENABLED = getattr(settings, 'IS_SMS_ENABLED', True)
            self.SMS_URL_TYPE = getattr(settings, 'SMS_URL_TYPE', 0)

    def __sms_ru_client(self, response: dict) -> None:
        if response['status'] == 'OK':
            self.notify.to_log(
                f"Статус основного запроса: {response['status']}, Код статуса: \
                {response['status_code']}, Баланс: {response['balance']}")
            for key in response['sms']:
                if response['sms'][key]['status'] == 'ERROR':
                    self.notify.to_log(
                        f"Ошибка у абонента: Номер: {key}, Статус: {response['sms'][key]['status']}, \
                        Код статуса: {response['sms'][key]['status_code']}, Описание: \
                        {response['sms'][key]['status_text']}")
            self.notify.state = STATE.DELIVERED
            self.notify.sent_at = now()
        else:
            self.notify.to_log(
                f"Статус: {response['status']}, Код статуса: {response['status_code']}, "
                f"Описание ошибки: {response['status_text']}")
            self.notify.state = STATE.REJECTED

    def __web_szk_client(self, response: Union[list, dict]) -> None:
        """
        Настройки/расшифровки ошибок по данному оператору можно посмотреть по адресу:
        https://stream-telecom.ru/solutions/integrations/
        """
        if not isinstance(response, list) and response.get('Code'):
            self.notify.to_log(f"Статус операции: {response}")
            self.notify.state = STATE.REJECTED
        else:
            self.notify.to_log(f"Статус операции: Успешно, ID отправленных сообщений: {response}")
            self.notify.state = STATE.DELIVERED
            self.notify.sent_at = now()

    def __iq_sms_client(self, response: dict) -> None:
        if response['status'] == 'ok':
            self.notify.to_log(
                f"Статус: {response['status']}, Код статуса: {response['code']}, Описание: \
                                   {response['description']}")
            self.notify.state = STATE.DELIVERED
            self.notify.sent_at = now()
        else:
            self.notify.to_log(
                f"Статус: {response['status']}, Код статуса: {response['code']}, "
                f"Описание ошибки: {response['description']}")
            self.notify.state = STATE.REJECTED

    def __sms_sending_client(self, response: dict) -> None:
        if response['code'] == 1:
            self.notify.to_log(
                f"Статус: {response['code']}, Описание: {response['descr']}")
            self.notify.state = STATE.DELIVERED
            self.notify.sent_at = now()
        else:
            self.notify.to_log(
                f"Статус: {response['code']}, Описание ошибки: {response['descr']}")
            self.notify.state = STATE.REJECTED

    def __sms_prosto_client(self, response: dict) -> None:
        if response['response']['msg']['err_code'] == 0:
            self.notify.to_log(
                f"Статус: {response['response']['msg']['err_code']}, Описание: \
                {response['response']['msg']['text']}")
            self.notify.state = STATE.DELIVERED
            self.notify.sent_at = now()
        else:
            self.notify.to_log(
                f"Статус: {response['response']['msg']['err_code']}, Описание ошибки: \
                {response['response']['msg']['text']}")
            self.notify.state = STATE.REJECTED

    def __send_sms(self):
        if not self.IS_SMS_ENABLED:
            self.notify.state = STATE.DISABLED
            self.notify.to_log('Not sent (sending is prohibited by settings)')
            return

        try:
            users_list = self.notify.users_list.all().order_by('-mail_to_all')
            if not users_list.exists():
                phones: str = self.notify.phone
            else:
                phones_list: list = ReceivingUsers.run_receiving_users(users_list, 'phone')
                phones = ','.join(phones_list)
            msg = str(self.notify.text.replace(' ', '+'))

            url: Optional[str] = SendData.sms_url(self.SMS_URL_TYPE).format(to=phones, text=msg)
            response: Response = requests.get(url)

            if self.SMS_URL_TYPE == SMS_URL.SMSRU_ID:
                self.__sms_ru_client(response.json())

            elif self.SMS_URL_TYPE == SMS_URL.WEBSZK_ID:
                self.__web_szk_client(response.json())

            elif self.SMS_URL_TYPE == SMS_URL.IQSMS_ID:
                self.__iq_sms_client(response.json())

            elif self.SMS_URL_TYPE == SMS_URL.INFOSMS_ID:
                self.notify.state = STATE.DELIVERED
                self.notify.sent_at = now()

            elif self.SMS_URL_TYPE == SMS_URL.SMSCENTRE_ID:
                self.notify.state = STATE.DELIVERED
                self.notify.sent_at = now()

            elif self.SMS_URL_TYPE == SMS_URL.SMS_SENDING_ID:
                self.__sms_sending_client(response.json())

            elif self.SMS_URL_TYPE == SMS_URL.SMS_PROSTO_ID:
                self.__sms_prosto_client(response.json())

        except Exception as e:
            self.notify.state = STATE.REJECTED
            self.notify.to_log(str(e))

    @classmethod
    def send_sms(cls, notify) -> None:
        """ Метод отправки SMS """
        cls(notify).__send_sms()
