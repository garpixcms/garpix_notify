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
        db_ids = set(
            SystemNotify.objects.filter(
                user=self.context['request'].user,
                type=TYPE.SYSTEM,
                state=STATE.DELIVERED,
                is_read=False
            ).values_list('id', flat=True)
        )
        ids = set(value)

        invalid_ids = ids.difference(db_ids)

        if len(invalid_ids) > 0:
            raise ValidationError(f"Уведомлений с id {', '.join(map(str, invalid_ids))} не существует")

        return value
