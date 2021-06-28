from django.contrib import admin
from fcm_django.models import FCMDevice
from ..models.fcm import NotifyDevice

admin.site.unregister(FCMDevice)


@admin.register(NotifyDevice)
class NotifyDeviceAdmin(admin.ModelAdmin):
    pass
