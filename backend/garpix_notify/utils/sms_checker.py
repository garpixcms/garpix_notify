import requests
from django.utils.timezone import now

from ..models.config import NotifyConfig
from garpix_notify.models.choices import STATE
from garpix_notify.utils import receiving

config = NotifyConfig.get_solo()


class SMSCLient:

    def send_sms(self):

        if not config.is_sms_enabled:
            self.state = STATE.DISABLED
            return

        try:
            print(self, 'Поехали')
            if self.users_list is None:
                print('пошел не туда')
                users_list = self.users_list.all()
                receivers = receiving(users_list)
                # Убираем дубликаты пользователей
                receivers = list({v['phone']: v for v in receivers}.values())
                phones = []
                for user in receivers:
                    if user['phone']:
                        phones.append(user['phone'])
                phones = ','.join(phones)
            else:
                phones = self.phone
                print(phones, 'елефоны')
            msg = str(self.text.replace(' ', '+'))
            if config.sms_url_type == NotifyConfig.SMS_URL.SMSRU_ID:
                url = '{url}?api_id={api_id}&to={to}&msg={text}&json=1'.format(
                    url=NotifyConfig.SMS_URL.SMSRU_URL,
                    api_id=config.sms_api_id,
                    from_text=config.sms_from,
                    to=phones,
                    text=msg,
                )
            elif config.sms_url_type == NotifyConfig.SMS_URL.INFOSMS_ID:
                url = '{url}?login={user}&pwd={pwd}&phones={to}&message={text}&sender={from_text}'.format(
                    url=NotifyConfig.SMS_URL.INFOSMS_URL,
                    user=config.sms_login,
                    pwd=config.sms_password,
                    from_text=config.sms_from,
                    to=phones,
                    text=msg,
                )
            elif config.sms_url_type == NotifyConfig.SMS_URL.IQSMS_ID:
                url = '{url}?login={user}&password={pwd}&phone={to}&text={text}'.format(
                    url=NotifyConfig.SMS_URL.IQSMS_URL,
                    user=config.sms_login,
                    pwd=config.sms_password,
                    to=phones,
                    text=msg,
                )
            elif config.sms_url_type == NotifyConfig.SMS_URL.SMSCENTRE_ID:
                url = '{url}?login={user}&psw={pwd}&phones={to}&mes={text}'.format(
                    url=NotifyConfig.SMS_URL.SMSCENTRE_URL,
                    user=config.sms_login,
                    pwd=config.sms_password,
                    to=phones,
                    text=msg,
                )
            elif config.sms_url_type == NotifyConfig.SMS_URL.SMS_SENDING_ID:
                url = '{url}?login={user}&password={pwd}&txt={text}&to={to}'.format(
                    url=NotifyConfig.SMS_URL.SMS_SENDING_URL,
                    user=config.sms_login,
                    pwd=config.sms_password,
                    to=phones,
                    text=msg,
                )
            else:
                url = '{url}?user={user}&pwd={pwd}&sadr={from_text}&text={text}&dadr={to}'.format(
                    url=NotifyConfig.SMS_URL.WEBSZK_URL,
                    user=config.sms_login,
                    pwd=config.sms_password,
                    from_text=config.sms_from,
                    to=phones,
                    text=msg,
                )
            print(url)
            response = requests.get(url)
            response_dict = response.json()
            print(response.json())
            print(response, 'ОТвет')
            try:
                if config.sms_url_type == NotifyConfig.SMS_URL.SMSRU_ID:
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
                if config.sms_url_type == NotifyConfig.SMS_URL.WEBSZK_ID:
                    try:
                        int(response.text)
                        self.state = STATE.DELIVERED
                        self.sent_at = now()
                    except Exception:
                        self.state = STATE.REJECTED
                if config.sms_url_type == NotifyConfig.SMS_URL.IQSMS_ID:
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
                if config.sms_url_type == NotifyConfig.SMS_URL.INFOSMS_ID:
                    #ответ в виде строки надо обработать
                    pass
                if config.sms_url_type == NotifyConfig.SMS_URL.SMSCENTRE_ID:
                    # ответ в виде строки надо обработать
                    pass
                if config.sms_url_type == NotifyConfig.SMS_URL.SMS_SENDING_ID:
                    if response_dict['code'] == 1:
                        self.to_log(
                            f"Статус: {response_dict['code']}, Описание: {response_dict['descr']}")
                        self.state = STATE.DELIVERED
                        self.sent_at = now()
                    else:
                        self.to_log(
                            f"Статус: {response_dict['code']}, Описание ошибки: {response_dict['descr']}")
                        self.state = STATE.REJECTED
            except Exception:
                self.state = STATE.REJECTED

        except Exception as e:  # noqa
            self.state = STATE.REJECTED
            self.to_log(str(e))
