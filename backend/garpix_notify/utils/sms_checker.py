import requests
from django.conf import settings
from django.utils.timezone import now

from garpix_notify.models.config import NotifyConfig
from garpix_notify.models.choices import STATE
from garpix_notify.utils.receiving import receiving_users

try:
    config = NotifyConfig.get_solo()
    IS_SMS_ENABLED = config.is_sms_enabled
    SMS_URL_TYPE = config.sms_url_type
    SMS_API_ID = config.sms_api_id
    SMS_LOGIN = config.sms_login
    SMS_PASSWORD = config.sms_password
    SMS_FROM = config.sms_from
except Exception:
    IS_SMS_ENABLED = True
    SMS_URL_TYPE = getattr(settings, 'SMS_URL_TYPE', 0)
    SMS_API_ID = getattr(settings, 'SMS_API_ID', 1234567890)
    SMS_LOGIN = getattr(settings, 'SMS_LOGIN', '')
    SMS_PASSWORD = getattr(settings, 'SMS_PASSWORD', '')
    SMS_FROM = getattr(settings, 'SMS_FROM', '')


class SMSCLient:

    def send_sms(self):  # noqa

        if not IS_SMS_ENABLED:
            self.state = STATE.DISABLED
            return

        try:
            users_list = self.users_list.all()
            if users_list.count() == 0:
                phones = self.phone
            else:
                receivers = receiving_users(users_list)
                # Убираем дубликаты пользователей
                receivers = list({v['phone']: v for v in receivers}.values())
                phones = []
                for user in receivers:
                    if user['phone']:
                        phones.append(user['phone'])
                phones = ','.join(phones)
            msg = str(self.text.replace(' ', '+'))
            if SMS_URL_TYPE == NotifyConfig.SMS_URL.SMSRU_ID:
                url = '{url}?api_id={api_id}&to={to}&msg={text}&json=1'.format(
                    url=NotifyConfig.SMS_URL.SMSRU_URL,
                    api_id=SMS_API_ID,
                    to=phones,
                    text=msg,
                )
            elif SMS_URL_TYPE == NotifyConfig.SMS_URL.INFOSMS_ID:
                url = '{url}?login={user}&pwd={pwd}&phones={to}&message={text}&sender={from_text}'.format(
                    url=NotifyConfig.SMS_URL.INFOSMS_URL,
                    user=SMS_LOGIN,
                    pwd=SMS_PASSWORD,
                    from_text=SMS_FROM,
                    to=phones,
                    text=msg,
                )
            elif SMS_URL_TYPE == NotifyConfig.SMS_URL.IQSMS_ID:
                url = '{url}?login={user}&password={pwd}&phone={to}&text={text}'.format(
                    url=NotifyConfig.SMS_URL.IQSMS_URL,
                    user=SMS_LOGIN,
                    pwd=SMS_PASSWORD,
                    to=phones,
                    text=msg,
                )
            elif SMS_URL_TYPE == NotifyConfig.SMS_URL.SMSCENTRE_ID:
                url = '{url}?login={user}&psw={pwd}&phones={to}&mes={text}'.format(
                    url=NotifyConfig.SMS_URL.SMSCENTRE_URL,
                    user=SMS_LOGIN,
                    pwd=SMS_PASSWORD,
                    to=phones,
                    text=msg,
                )
            elif SMS_URL_TYPE == NotifyConfig.SMS_URL.SMS_SENDING_ID:
                url = '{url}?login={user}&password={pwd}&txt={text}&to={to}'.format(
                    url=NotifyConfig.SMS_URL.SMS_SENDING_URL,
                    user=SMS_LOGIN,
                    pwd=SMS_PASSWORD,
                    to=phones,
                    text=msg,
                )
            elif SMS_URL_TYPE == NotifyConfig.SMS_URL.SMS_PROSTO_ID:
                url = '{url}?method=push_msg&format=json&key={api_id}&text={text}&phone={to}&sender_name={from_text}'.format(
                    url=NotifyConfig.SMS_URL.SMS_PROSTO_URL,
                    api_id=SMS_API_ID,
                    from_text=SMS_FROM,
                    to=phones,
                    text=msg,
                )
            else:
                url = '{url}?user={user}&pwd={pwd}&sadr={from_text}&text={text}&dadr={to}'.format(
                    url=NotifyConfig.SMS_URL.WEBSZK_URL,
                    user=SMS_LOGIN,
                    pwd=SMS_PASSWORD,
                    from_text=SMS_FROM,
                    to=phones,
                    text=msg,
                )
            response = requests.get(url)
            response_dict = response.json()
            try:
                if SMS_URL_TYPE == NotifyConfig.SMS_URL.SMSRU_ID:
                    if response_dict['status'] == 'OK':
                        self.to_log(
                            f"Статус: {response_dict['status']}, Код статуса: {response_dict['status_code']}, Описание: {response_dict['status_text']}")
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
