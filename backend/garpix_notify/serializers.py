from rest_framework import serializers

from garpix_notify.models import SystemNotify


class SystemNotifySerializer(serializers.ModelSerializer):

    class Meta:
        model = SystemNotify
        fields = '__all__'
