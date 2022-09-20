from django.conf import settings

from garpix_notify.models.choices import CALL_URL, SMS_URL
from garpix_notify.models.config import NotifyConfig


class SendDataService:
    def __int__(self):
        try:
            config = NotifyConfig.get_solo()
            SMS_API_ID = config.sms_api_id
            SMS_LOGIN = config.sms_login
            SMS_PASSWORD = config.sms_password
            SMS_FROM = config.sms_from
        except Exception:
            SMS_API_ID = getattr(settings, 'SMS_API_ID', 1234567890)
            SMS_LOGIN = getattr(settings, 'SMS_LOGIN', '')
            SMS_PASSWORD = getattr(settings, 'SMS_PASSWORD', '')
            SMS_FROM = getattr(settings, 'SMS_FROM', '')

        try:
            config = NotifyConfig.get_solo()
            CALL_API_ID = config.call_api_id
            CALL_LOGIN = config.call_login
            CALL_PASSWORD = config.call_password
        except Exception:
            CALL_API_ID = getattr(settings, 'CALL_API_ID', 1234567890)
            CALL_LOGIN = getattr(settings, 'CALL_LOGIN', '')
            CALL_PASSWORD = getattr(settings, 'CALL_PASSWORD', '')

        self.url_dict_call = {
            0: '{url}?phone={to}&api_id={api_id}&json=1',
            1: '{url}?phone={to}&login={login}&password={password}&json=1',
            2: '{url}?login={login}&psw={password}&phones={to}&mes=code&call=1&fmt=3',
            3: '{url}?phone={to}&key={password}&service_id={login}',
        }

        self.operator_call = {
            0: {
                'url': CALL_URL.SMSRU_CALL_URL,
                'api_id': CALL_API_ID},
            1: {
                'url': CALL_URL.SMSRU_CALL_URL,
                'login': CALL_LOGIN,
                'password': CALL_PASSWORD},
            2: {
                'url': CALL_URL.SMSCENTRE_URL,
                'login': CALL_LOGIN,
                'password': CALL_PASSWORD},
            3: {
                'url': CALL_URL.UCALLER_URL,
                'login': CALL_LOGIN,
                'password': CALL_PASSWORD}}

        self.url_dict_sms = {
            0: '{url}?api_id={api_id}&to={to}&msg={text}&json=1',
            1: '{url}?login={user}&pwd={pwd}&phones={to}&message={text}&sender={from_text}',
            2: '{url}?login={user}&password={pwd}&phone={to}&text={text}',
            3: '{url}?login={user}&psw={pwd}&phones={to}&mes={text}',
            4: '{url}?login={user}&password={pwd}&txt={text}&to={to}',
            5: '{url}?method=push_msg&format=json&key={api_id}&text={text}&phone={to}&sender_name={from_text}',
            6: '{url}?user={user}&pwd={pwd}&sadr={from_text}&text={text}&dadr={to}',
        }

        self.operator_sms = {
            0: {
                'url': SMS_URL.SMSRU_URL,
                'api_id': SMS_API_ID},
            1: {
                'url': SMS_URL.INFOSMS_URL,
                'user': SMS_LOGIN,
                'pwd': SMS_PASSWORD,
                'from_text': SMS_FROM},
            2: {
                'url': SMS_URL.IQSMS_URL,
                'user': SMS_LOGIN,
                'pwd': SMS_PASSWORD},
            3: {
                'url': SMS_URL.SMSCENTRE_URL,
                'user': SMS_LOGIN,
                'pwd': SMS_PASSWORD},
            4: {
                'url': SMS_URL.SMS_SENDING_URL,
                'user': SMS_LOGIN,
                'pwd': SMS_PASSWORD},
            5: {
                'url': SMS_URL.SMS_PROSTO_URL,
                'user': SMS_LOGIN,
                'pwd': SMS_PASSWORD,
                'from_text': SMS_FROM},
            6: {
                'url': SMS_URL.WEBSZK_URL,
                'user': SMS_LOGIN,
                'pwd': SMS_PASSWORD,
                'from_text': SMS_FROM},
        }

    @staticmethod
    def response_check(response, operator_type, status):
        if status == 0:
            response_processing = {
                0 or 1: {
                    'Status': response.get('status'),
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
            return response_processing[operator_type]

        if status == 1:
            response_processing = {
                0 or 1: {
                    'Status': response.get('status'),
                    'Status_code': response.get('status_code'),
                    'Status_text': response.get('status_text')},
                2: {'Status': response.get('status'),
                    'Status_code': response.get('error_code'),
                    'Status_text': response.get('error')},
                3: {'Status': response.get('status'),
                    'Status_code': response.get('code'),
                    'Status_text': response.get('error')}}
            return response_processing[operator_type]

        return None
