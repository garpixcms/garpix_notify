import pytest
from django.utils import timezone
from django.test.client import Client

from ..models.system_notify import SystemNotify
from ..models import Notify
from ..models.choices import STATE, TYPE
from .utils.common_class import CommonTestClass
from .utils.generate_data import generate_users
from ..tasks import send_notifications


@pytest.mark.django_db
class TestSystemNotifyView(CommonTestClass):
    @pytest.fixture
    def users(self, client: Client):
        data_users = generate_users(2)
        user = self.create_user(data_users[0])
        other_user = self.create_user(data_users[1])
        client.force_login(user)
        return user, other_user

    @pytest.fixture
    def system_notifications(self, users):
        user, other_user = users
        return SystemNotify.objects.bulk_create([
            SystemNotify(user=user, type=TYPE.SYSTEM, state=STATE.DELIVERED),
            SystemNotify(user=user, type=TYPE.SYSTEM, state=STATE.DELIVERED),
            SystemNotify(user=user, type=TYPE.SYSTEM, state=STATE.WAIT),
            SystemNotify(user=other_user, type=TYPE.SYSTEM, state=STATE.DELIVERED),
        ])

    def test_list_notifications(self, client: Client, system_notifications):
        response = client.get('/api/garpix_notify/system_notifies/')
        result = response.json()

        assert response.status_code == 200
        assert result[0]['id'] == system_notifications[1].pk
        assert result[1]['id'] == system_notifications[0].pk
        assert len(result) == 2

    def test_read(self, client: Client, system_notifications):
        assert system_notifications[0].is_read is False
        assert system_notifications[1].is_read is False
        assert system_notifications[2].is_read is False
        assert system_notifications[3].is_read is False

        response = client.post('/api/garpix_notify/system_notifies/read/', {'ids': [system_notifications[0].pk, system_notifications[1].pk]})

        system_notifications[0].refresh_from_db()
        system_notifications[1].refresh_from_db()
        system_notifications[2].refresh_from_db()
        system_notifications[3].refresh_from_db()

        assert response.status_code == 200
        assert system_notifications[0].is_read is True
        assert system_notifications[1].is_read is True
        assert system_notifications[2].is_read is False
        assert system_notifications[3].is_read is False

    def test_read_invalid_ids(self, client: Client, system_notifications):
        response = client.post('/api/garpix_notify/system_notifies/read/', {'ids': [system_notifications[0].pk, system_notifications[2].pk, system_notifications[3].pk]})
        result = response.json()

        assert response.status_code == 400
        assert result == {
            'ids': [f'Уведомлений с id {", ".join([str(system_notifications[2].pk), str(system_notifications[3].pk)])} не существует'],
        }

    def test_read_all(self, client: Client, system_notifications):
        assert system_notifications[0].is_read is False
        assert system_notifications[1].is_read is False
        assert system_notifications[2].is_read is False
        assert system_notifications[3].is_read is False

        response = client.post('/api/garpix_notify/system_notifies/read_all/')

        system_notifications[0].refresh_from_db()
        system_notifications[1].refresh_from_db()
        system_notifications[2].refresh_from_db()
        system_notifications[3].refresh_from_db()

        assert response.status_code == 200
        assert system_notifications[0].is_read is True
        assert system_notifications[1].is_read is True
        assert system_notifications[2].is_read is False
        assert system_notifications[3].is_read is False
