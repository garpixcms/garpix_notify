from django.conf import settings

from garpix_notify.models.config import NotifyConfig

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

url_dict = {
    0: '{url}?phone={to}&api_id={api_id}&json=1',
    1: '{url}?phone={to}&login={login}&password={password}&json=1',
    2: '{url}?login={login}&psw={password}&phones={to}&mes=code&call=1&fmt=3',
    3: '{url}?phone={to}&key={password}&service_id={login}',
}

operator = {
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
        'password': CALL_PASSWORD},
}