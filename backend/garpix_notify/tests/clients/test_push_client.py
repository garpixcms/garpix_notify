import datetime
import pytest
import telegram
from unittest.mock import Mock, MagicMock, patch
from ...models.fcm import NotifyDevice
from garpix_notify.models import Notify, NotifyConfig, NotifyErrorLog
from garpix_notify.models.choices import STATE, PARSE_MODE_TELEGRAM
from garpix_notify.clients import PushClient
from ..utils.common_class import CommonTestClass
from ..utils.generate_data import (
    generate_users, generate_category, generate_system_notify_data, generate_system_template_data,
)


@pytest.mark.django_db
class TestPushClient(CommonTestClass):
    @pytest.fixture
    def setup(self):
        # Tests Events
        self.PASS_TEST_EVENT = 1

        # Users data
        self.user = self.create_user(generate_users(1)[0])
        self.user_list = self.create_system_user_list()

        # Data for test user
        self.some_data_dict = generate_system_notify_data()
        self.data_category = generate_category()[0]

        self.data_template = generate_system_template_data(self.some_data_dict, self.PASS_TEST_EVENT)[0]

        # Creating templates/category
        self.category_1 = self.create_category(self.data_category)
        self.template_1 = self.create_template(self.data_template, self.category_1)

        self.notify = Notify.send(event=self.PASS_TEST_EVENT, context={}, user=self.user)[0]
        self.notify_config = NotifyConfig.get_solo()

    def test_send_disabled_via_config(self, setup: None):
        self.notify_config.is_push_enabled = False
        self.notify_config.save()

        PushClient.send_push(self.notify)

        assert self.notify.state == STATE.DISABLED
        assert NotifyErrorLog.objects.filter(notify=self.notify, error='Not sent (sending is prohibited by settings)').exists()

    @patch('garpix_notify.clients.push_client.now')
    def test_send_successfull(self, now_mock: Mock, setup: None):
        now_time = datetime.datetime(2024, 7, 30, 12, 0, 0)
        now_mock.return_value = now_time

        PushClient.send_push(self.notify)

        assert self.notify.state == STATE.DELIVERED
        assert self.notify.sent_at == now_time
