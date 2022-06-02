from django.conf import settings

from garpix_notify.models.config import NotifyConfig

try:
    config = NotifyConfig.get_solo()
    CALL_URL_TYPE = config.call_url_type
    CALL_API_ID = config.call_api_id
    CALL_LOGIN = config.call_login
    CALL_PASSWORD = config.call_password
    SMS_URL_TYPE = config.sms_url_type
    SMS_API_ID = config.sms_api_id
    SMS_LOGIN = config.sms_login
    SMS_PASSWORD = config.sms_password
    SMS_FROM = config.sms_from
except Exception:
    CALL_URL_TYPE = getattr(settings, 'CALL_URL_TYPE', 0)
    CALL_API_ID = getattr(settings, 'CALL_API_ID', 1234567890)
    CALL_LOGIN = getattr(settings, 'CALL_LOGIN', '')
    CALL_PASSWORD = getattr(settings, 'CALL_PASSWORD', '')
    CALL_FROM = getattr(settings, 'CALL_FROM', '')
    SMS_URL_TYPE = getattr(settings, 'SMS_URL_TYPE', 0)
    SMS_API_ID = getattr(settings, 'SMS_API_ID', 1234567890)
    SMS_LOGIN = getattr(settings, 'SMS_LOGIN', '')
    SMS_PASSWORD = getattr(settings, 'SMS_PASSWORD', '')
    SMS_FROM = getattr(settings, 'SMS_FROM', '')

url_dict_call = {
    0: '{url}?phone={to}&api_id={api_id}&json=1',
    1: '{url}?phone={to}&login={login}&password={password}&json=1',
    2: '{url}?login={login}&psw={password}&phones={to}&mes=code&call=1&fmt=3',
    3: '{url}?phone={to}&key={password}&service_id={login}',
}

operator_call = {
    0: {
        'url': NotifyConfig.CALL_URL.SMSRU_CALL_URL,
        'api_id': CALL_API_ID},
    1: {
        'url': NotifyConfig.CALL_URL.SMSRU_CALL_URL,
        'login': CALL_LOGIN,
        'password': CALL_PASSWORD},
    2: {
        'url': NotifyConfig.CALL_URL.SMSCENTRE_URL,
        'login': CALL_LOGIN,
        'password': CALL_PASSWORD},
    3: {
        'url': NotifyConfig.CALL_URL.UCALLER_URL,
        'login': CALL_LOGIN,
        'password': CALL_PASSWORD}}


url_dict_sms = {
    0: '{url}?api_id={api_id}&to={to}&msg={text}&json=1',
    1: '{url}?login={user}&pwd={pwd}&phones={to}&message={text}&sender={from_text}',
    2: '{url}?login={user}&password={pwd}&phone={to}&text={text}',
    3: '{url}?login={user}&psw={pwd}&phones={to}&mes={text}',
    4: '{url}?login={user}&password={pwd}&txt={text}&to={to}',
    5: '{url}?method=push_msg&format=json&key={api_id}&text={text}&phone={to}&sender_name={from_text}',
    6: '{url}?user={user}&pwd={pwd}&sadr={from_text}&text={text}&dadr={to}',
}

operator_sms = {
    0: {
        'url': NotifyConfig.SMS_URL.SMSRU_URL,
        'api_id': CALL_API_ID},
    1: {
        'url': NotifyConfig.SMS_URL.INFOSMS_URL,
        'user': SMS_LOGIN,
        'pwd': SMS_PASSWORD,
        'from_text': SMS_FROM},
    2: {
        'url': NotifyConfig.SMS_URL.IQSMS_URL,
        'user': SMS_LOGIN,
        'pwd': SMS_PASSWORD},
    3: {
        'url': NotifyConfig.SMS_URL.SMSCENTRE_URL,
        'user': SMS_LOGIN,
        'pwd': SMS_PASSWORD},
    4: {
        'url': NotifyConfig.SMS_URL.SMS_SENDING_URL,
        'user': SMS_LOGIN,
        'pwd': SMS_PASSWORD},
    5: {
        'url': NotifyConfig.SMS_URL.SMS_PROSTO_URL,
        'user': SMS_LOGIN,
        'pwd': SMS_PASSWORD,
        'from_text': SMS_FROM},
    6: {
        'url': NotifyConfig.SMS_URL.WEBSZK_URL,
        'user': SMS_LOGIN,
        'pwd': SMS_PASSWORD,
        'from_text': SMS_FROM},
}
