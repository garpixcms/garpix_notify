from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from garpix_notify.models import SystemNotify
from garpix_notify.models.choices import TYPE, STATE


class SystemNotifySerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemNotify
        fields = '__all__'


class ReadSystemNotifySerializer(serializers.Serializer):
    ids = serializers.ListField(child=serializers.IntegerField(), allow_empty=False)

    def validate_ids(self, value):
        db_ids = SystemNotify.objects.filter(user=self.context['request'].user, type=TYPE.SYSTEM, state=STATE.DELIVERED,
                                             is_read=False).values_list('id', flat=True)

        for id_val in value:
            if id_val not in db_ids:
                raise ValidationError(f"Уведомление с id {id_val} не муществует")

        return value
