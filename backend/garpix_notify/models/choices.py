class TYPE:
    EMAIL = 0
    SMS = 1
    PUSH = 2
    TELEGRAM = 3
    VIBER = 4
    SYSTEM = 5
    CALL = 6
    WHATSAPP = 7

    CHOICES = (
        (EMAIL, 'E-mail'),
        (SMS, 'SMS'),
        (PUSH, 'Push'),
        (TELEGRAM, 'Telegram'),
        (VIBER, 'Viber'),
        (SYSTEM, 'System'),
        (CALL, 'Call'),
        (WHATSAPP, 'WhatsApp')
    )


class STATE:
    DISABLED = -2
    REJECTED = -1
    WAIT = 0
    DELIVERED = 1

    CHOICES = (
        (DELIVERED, 'Доставлено'),
        (REJECTED, 'Отклонено'),
        (WAIT, 'В ожидании'),
        (DISABLED, 'Не отправлено (отправка запрещена настройками)'),
    )


class EMAIL_MALLING:
    CC = 0
    BCC = 1
    TYPES = (
        (CC, 'Обычная рассылка'),
        (BCC, 'Скрытая рассылка'),
    )


class PARSE_MODE_TELEGRAM:
    """ Выбор метода парсинга телеграмм сообщений"""

    EMPTY = ''
    HTML = 'HTML'
    MARKDOWN = 'Markdown'

    TYPES = (
        (EMPTY, 'Без форматирования'),
        (HTML, 'HTML'),
        (MARKDOWN, 'Markdown'),
    )


class SMS_URL:
    """ URL СМС провайдера """

    SMSRU_ID = 0
    WEBSZK_ID = 1
    IQSMS_ID = 2
    INFOSMS_ID = 3
    SMSCENTRE_ID = 4
    SMS_SENDING_ID = 5
    SMS_PROSTO_ID = 6

    SMSRU_URL = 'https://sms.ru/sms/send/'
    WEBSZK_URL = 'https://gateway.api.sc/rest/Send/SendSms/'
    IQSMS_URL = 'https://api.iqsms.ru/messages/v2/send.json'
    INFOSMS_URL = 'http://api.infosmska.ru/interfaces/SendMessages.ashx'
    SMSCENTRE_URL = 'https://smsc.ru/sys/send.php'
    SMS_SENDING_URL = 'http://lcab.sms-sending.ru/lcabApi/sendSms.php'
    SMS_PROSTO_URL = 'http://api.sms-prosto.ru/'

    TYPES = (
        (SMSRU_ID, 'sms.ru'),
        (WEBSZK_ID, 'web.szk-info.ru'),
        (IQSMS_ID, 'iqsms.ru'),
        (INFOSMS_ID, 'infosmska.ru'),
        (SMSCENTRE_ID, 'smsc.ru'),
        (SMS_SENDING_ID, 'sms-sending.ru'),
        (SMS_PROSTO_ID, 'sms-prosto.ru')
    )


class CALL_URL:
    """ URL Оператора связи """
    SMSRU_CALL_API_ID = 0
    SMSRU_CALL_ID = 1
    SMSCENTRE_ID = 2
    UCALLER_ID = 3

    SMSRU_CALL_URL = 'https://sms.ru/code/call'
    SMSCENTRE_URL = 'https://smsc.ru/sys/send.php'
    UCALLER_URL = 'https://api.ucaller.ru/v1.0/initCall'

    TYPES = (
        (SMSRU_CALL_API_ID, 'sms.ru API'),
        (SMSRU_CALL_ID, 'sms.ru LOGIN'),
        (SMSCENTRE_ID, 'smsc.ru'),
        (UCALLER_ID, 'ucaller.ru'),

    )


class StatusMessage:
    """ Статус сообщения """
    STATUS = {
        STATE.DISABLED: '<span style="color:red;">Отправка запрещена</span>',
        STATE.REJECTED: '<span style="color:red;">Отклонено</span>',
        STATE.WAIT: '<span style="color:orange;">В ожидании</span>',
        STATE.DELIVERED: '<span style="color:green;">Отправлено</span>',
    }
