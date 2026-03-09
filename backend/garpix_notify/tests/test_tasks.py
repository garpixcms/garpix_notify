import pytest
from unittest.mock import patch

from garpix_notify.models import Notify
from garpix_notify.models.choices import STATE, TYPE
from garpix_notify.tasks.tasks import send_notify_now
from .utils.common_class import CommonTestClass
from .utils.generate_data import generate_category, generate_users


@pytest.mark.django_db
class TestSendNotifyNow(CommonTestClass):

    @pytest.fixture
    def notify_wait(self):
        """Создаёт уведомление в состоянии WAIT."""
        user = self.create_user(generate_users(1)[0])
        category = self.create_category(generate_category()[0])
        return Notify.objects.create(
            subject='Test',
            text='Test text',
            html='<p>Test</p>',
            type=TYPE.EMAIL,
            category=category,
            user=user,
            email=user.email,
            state=STATE.WAIT,
        )

    def test_send_notify_now_calls_start_send_for_wait_notify(self, notify_wait):
        """Задача вызывает start_send для уведомления в состоянии WAIT."""
        with patch.object(Notify, 'start_send') as mock_start_send:
            send_notify_now(notify_wait.pk)
            mock_start_send.assert_called_once()

    def test_send_notify_now_does_nothing_for_non_existent_pk(self):
        """Задача не падает при несуществующем pk."""
        send_notify_now(999999)

    def test_send_notify_now_does_nothing_for_delivered_notify(self, notify_wait):
        """Задача не вызывает start_send для уже доставленного уведомления."""
        notify_wait.state = STATE.DELIVERED
        notify_wait.save()

        with patch.object(Notify, 'start_send') as mock_start_send:
            send_notify_now(notify_wait.pk)
            mock_start_send.assert_not_called()

    def test_send_notify_now_does_nothing_for_rejected_notify(self, notify_wait):
        """Задача не вызывает start_send для отклонённого уведомления."""
        notify_wait.state = STATE.REJECTED
        notify_wait.save()

        with patch.object(Notify, 'start_send') as mock_start_send:
            send_notify_now(notify_wait.pk)
            mock_start_send.assert_not_called()
