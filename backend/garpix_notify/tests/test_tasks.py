import pytest
from django.utils import timezone
from ..models import Notify
from ..models.choices import STATE, TYPE
from .utils.common_class import CommonTestClass
from .utils.generate_data import generate_category
from ..tasks import send_notifications


@pytest.mark.django_db
class TestTasks(CommonTestClass):
    @pytest.fixture
    def category(self):
        data_category = generate_category()[0]
        return self.create_category(data_category)

    @pytest.fixture
    def notifications(self, category):
        return Notify.objects.bulk_create([
            Notify(category=category, text='test1', type=TYPE.EMAIL, send_at=timezone.now()),
            Notify(category=category, text='test2', type=TYPE.SYSTEM, send_at=timezone.now()),
            Notify(category=category, text='test3', type=TYPE.EMAIL, send_at=None),
            Notify(category=category, text='test4', type=TYPE.EMAIL, send_at=None, state=STATE.DELIVERED),
        ])

    def test_send_notifications(self, notifications):
        send_notifications()

        pks = (notifications[0].pk, notifications[2].pk)

        assert 2 == Notify.objects.filter(pk__in=pks, state=STATE.DISABLED).count()
