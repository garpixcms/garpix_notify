from typing import Optional
from django.conf import settings
from django.db import DatabaseError, ProgrammingError

from garpix_notify.models.choices import CALL_URL, SMS_URL
from garpix_notify.models.config import NotifyConfig


class SendData:
    """
    Класс формирует ссылку для обращения на API оператора.
    """

    def __init__(self):
        try:
            self.config = NotifyConfig.get_solo()
            self.SMS_API_ID = self.config.sms_api_id
            self.SMS_LOGIN = self.config.sms_login
            self.SMS_PASSWORD = self.config.sms_password
            self.SMS_FROM = self.config.sms_from
        except (DatabaseError, ProgrammingError):
            self.SMS_API_ID = getattr(settings, 'SMS_API_ID', 1234567890)
            self.SMS_LOGIN = getattr(settings, 'SMS_LOGIN', '')
            self.SMS_PASSWORD = getattr(settings, 'SMS_PASSWORD', '')
            self.SMS_FROM = getattr(settings, 'SMS_FROM', '')
        try:
            self.CALL_API_ID = self.config.call_api_id
            self.CALL_LOGIN = self.config.call_login
            self.CALL_PASSWORD = self.config.call_password
        except (DatabaseError, ProgrammingError):
            self.CALL_API_ID = getattr(settings, 'CALL_API_ID', 1234567890)
            self.CALL_LOGIN = getattr(settings, 'CALL_LOGIN', '')
            self.CALL_PASSWORD = getattr(settings, 'CALL_PASSWORD', '')
            self.CALL_FROM = getattr(settings, 'CALL_FROM', '')

    def __get_call_url(self, key: int) -> Optional[str]:
        url_dict_call = {
            CALL_URL.SMSRU_CALL_API_ID: (f'{CALL_URL.SMSRU_CALL_URL}?api_id={self.CALL_API_ID}' + '&phone={to}&json=1'),
            CALL_URL.SMSRU_CALL_ID: (f'{CALL_URL.SMSRU_CALL_URL}?login={self.CALL_LOGIN}&password={self.CALL_PASSWORD}' + '&phone={to}&json=1'),
            CALL_URL.SMSCENTRE_ID: (f'{CALL_URL.SMSCENTRE_URL}?login={self.CALL_LOGIN}&psw={self.CALL_PASSWORD}' + '&phones={to}&mes=code&call=1&fmt=3'),
            CALL_URL.UCALLER_ID: (f'{CALL_URL.UCALLER_URL}?key={self.CALL_PASSWORD}&service_id={self.CALL_LOGIN}' + '&phone={to}'),
        }
        return url_dict_call.get(key, str())

    def __get_sms_url(self, key: int) -> Optional[str]:
        url_dict_sms = {
            SMS_URL.SMSRU_ID: (f'{SMS_URL.SMSRU_URL}?api_id={self.SMS_API_ID}' + '&to={to}&msg={text}&json=1'),
            SMS_URL.WEBSZK_ID: (f'{SMS_URL.WEBSZK_URL}?login={self.SMS_LOGIN}&pass={self.SMS_PASSWORD}&sourceAddress={self.SMS_FROM}' + '&destinationAddress={to}&data={text}'),
            SMS_URL.IQSMS_ID: (f'{SMS_URL.IQSMS_URL}?login={self.SMS_LOGIN}&password={self.SMS_PASSWORD}' + '&phone={to}&text={text}'),
            SMS_URL.INFOSMS_ID: (f'{SMS_URL.INFOSMS_URL}?login={self.SMS_LOGIN}&pwd={self.SMS_PASSWORD}&sender={self.SMS_FROM}' + '&phones={to}&message={text}'),
            SMS_URL.SMSCENTRE_ID: (f'{SMS_URL.SMSCENTRE_URL}?login={self.SMS_LOGIN}&psw={self.SMS_PASSWORD}' + '&phones={to}&mes={text}'),
            SMS_URL.SMS_SENDING_ID: (f'{SMS_URL.SMS_SENDING_URL}?login={self.SMS_LOGIN}&password={self.SMS_PASSWORD}' + '&txt={text}&to={to}'),
            SMS_URL.SMS_PROSTO_ID: (f'{SMS_URL.SMS_PROSTO_URL}?login={self.SMS_LOGIN}&password={self.SMS_PASSWORD}&method=push_msg&format=json&sender_name={self.SMS_FROM}' + 'text={text}&phone={to}&key={api_id}'),
        }
        return url_dict_sms.get(key, str())

    @classmethod
    def call_url(cls, url_type: int) -> Optional[str]:
        """ Метод формирует URL оператора для отправки звонка """
        return cls().__get_call_url(url_type)

    @classmethod
    def sms_url(cls, url_type: int) -> Optional[str]:
        """ Метод формирует URL оператора для отправки SMS """
        return cls().__get_sms_url(url_type)
