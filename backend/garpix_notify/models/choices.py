class TYPE:
    EMAIL = 0
    SMS = 1
    PUSH = 2
    TELEGRAM = 3
    VIBER = 4
    SYSTEM = 5
    CALL = 6

    CHOICES = (
        (EMAIL, 'E-mail'),
        (SMS, 'SMS'),
        (PUSH, 'Push'),
        (TELEGRAM, 'Telegram'),
        (VIBER, 'Viber'),
        (SYSTEM, 'System'),
        (CALL, 'Call'),
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
