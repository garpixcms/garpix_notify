class TYPE:
    EMAIL = 0
    SMS = 1
    PUSH = 2
    TELEGRAM = 3
    VIBER = 4

    CHOICES = (
        (EMAIL, 'E-mail'),
        (SMS, 'SMS'),
        (PUSH, 'Push'),
        (TELEGRAM, 'Telegram'),
        (VIBER, 'Viber'),
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
