import requests
import enum

from typing import Optional, Tuple
from django.conf import settings
from django.db import DatabaseError, ProgrammingError
from django.utils.timezone import now

from garpix_notify.models.config import NotifyConfig
from garpix_notify.utils.send_data import SendData
from garpix_notify.models.choices import STATE, CALL_URL


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
        except (DatabaseError, ProgrammingError):
            self.IS_CALL_ENABLED = getattr(settings, 'IS_CALL_ENABLED', True)
            self.CALL_URL_TYPE = getattr(settings, 'CALL_URL_TYPE', 0)

    def __value_checker(self, response_dict: dict) -> Optional[int]:
        value: Optional[int] = None

        if self.CALL_URL_TYPE in (CALL_URL.SMSRU_CALL_ID, CALL_URL.SMSRU_CALL_API_ID):
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

    def __response_check(self, response: dict, status: int) -> dict:
        if status == self.ChoiceValue.OK.value:
            response_processing: dict = {
                0: {'Status': response.get('status'),
                    'Code': response.get('code'),
                    'Balance': response.get('balance'),
                    'ID_Call': response.get('call_id')},
                1: {'Status': response.get('status'),
                    'Code': response.get('code'),
                    'Balance': response.get('balance'),
                    'ID_Call': response.get('call_id')},

                2: {'Status': response.get('id'),
                    'Code': response.get('code'),
                    'ID_Call': response.get('cnt'),
                    'Balance': response.get('balance')},

                3: {'Status': response.get('status'),
                    'Code': response.get('code'),
                    'Balance': response.get('balance'),
                    'ID_Call': response.get('unique_request_id')}}

        else:
            response_processing: dict = {
                0: {'Status': response.get('status'),
                    'Status_code': response.get('status_code'),
                    'Status_text': response.get('status_text')},
                1: {'Status': response.get('status'),
                    'Status_code': response.get('status_code'),
                    'Status_text': response.get('status_text')},
                2: {'Status': response.get('status'),
                    'Status_code': response.get('error_code'),
                    'Status_text': response.get('error')},
                3: {'Status': response.get('status'),
                    'Status_code': response.get('code'),
                    'Status_text': response.get('error')}}

        return response_processing[self.CALL_URL_TYPE]

    def __send_call_code(self) -> None:

        if not self.IS_CALL_ENABLED:
            self.notify.state = STATE.DISABLED
            self.notify.to_log('Not sent (sending is prohibited by settings)')
            return

        phone = str(self.notify.phone)

        try:
            send_data = SendData()
            url = send_data.call_url(self.CALL_URL_TYPE).format(to=phone)
            response_url = requests.get(url)
            response_dict = response_url.json()
            value = self.__value_checker(response_dict)
            response = self.__response_check(response_dict, value)
            self.__save_to_log(response, value)
        except Exception as e:
            self.notify.state = STATE.REJECTED
            self.notify.to_log(str(e))

    def __save_to_log(self, response: dict, value: int) -> None:
        if value == self.ChoiceValue.OK.value:
            self.notify.to_log(
                'Status: {Status}, Code: {Code}, Balance: {Balance}, ID_Call: {ID_Call}'.format(**response)
            )
            self.notify.state = STATE.DELIVERED
            self.notify.sent_at = now()
        elif value == self.ChoiceValue.BAD.value:
            self.notify.to_log(
                'Status: {Status}, Status_code: {Status_code}, Status_text: {Status_text}'.format(**response)
            )
            self.notify.state = STATE.REJECTED

    @classmethod
    def get_value_checker(cls, response_dict: dict) -> Tuple[Optional[int], dict]:
        call_client_empty = cls(notify=None)
        value = call_client_empty.__value_checker(response_dict)
        return value, call_client_empty.__response_check(response_dict, value)

    @classmethod
    def get_url_type(cls) -> int:
        return cls(notify=None).CALL_URL_TYPE

    @classmethod
    def send_call(cls, notify) -> None:
        cls(notify).__send_call_code()
