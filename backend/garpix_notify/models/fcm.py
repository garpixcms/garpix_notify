from fcm_django.models import FCMDevice


class NotifyDevice(FCMDevice):
    """
    Переопределен Класс для того чтобы спрятать модель в другое приложение
    """

    class Meta:
        proxy = True
        verbose_name = 'FCM аккаунт'
        verbose_name_plural = 'FCM аккаунты'
