

def sms_checker(msg, phones, config, NotifyConfig):
    if config.sms_url_type == NotifyConfig.SMS_URL.SMSRU_ID:
        url = '{url}?msg={text}&to={to}&api_id={api_id}&from={from_text}&json=1'.format(
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
    return url
