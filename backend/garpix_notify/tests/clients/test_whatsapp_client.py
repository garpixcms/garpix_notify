import datetime
import pytest
from unittest.mock import Mock, MagicMock, PropertyMock, patch
from garpix_notify.models import Notify, NotifyConfig, NotifyErrorLog
from garpix_notify.models.choices import STATE
from garpix_notify.clients import WhatsAppClient
from ..utils.common_class import CommonTestClass
from ..utils.generate_data import (
    generate_users, generate_category, generate_system_notify_data, generate_system_template_data,
)


@pytest.mark.django_db
class TestWhatsAppClient(CommonTestClass):
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
        self.notify_config.is_whatsapp_enabled = True
        self.notify_config.whatsapp_auth_token = 'test-api-key'
        self.notify_config.whatsapp_account_sid = 'test-name'
        self.notify_config.whatsapp_sender = 'test-sender'
        self.notify_config.save()

    def test_send_disabled_via_config(self, setup: None):
        self.notify_config.is_whatsapp_enabled = False
        self.notify_config.save()

        WhatsAppClient.send_whatsapp(self.notify)

        assert self.notify.state == STATE.DISABLED
        assert NotifyErrorLog.objects.filter(notify=self.notify, error='Not sent (sending is prohibited by settings)').exists()

    @patch('garpix_notify.clients.whatsapp_client.now')
    @patch('garpix_notify.clients.whatsapp_client.Client')
    def test_send_successfull(self, bot_mock: Mock, now_mock: Mock, setup: None):
        now_time = datetime.datetime(2024, 7, 30, 12, 0, 0)
        now_mock.return_value = now_time
        response = MagicMock()
        type(response).sid = PropertyMock(return_value=True)
        bot_instance = MagicMock()
        bot_instance.messages.create = MagicMock()
        bot_instance.messages.create.return_value = response
        bot_mock.return_value = bot_instance

        WhatsAppClient.send_whatsapp(self.notify)

        bot_mock.assert_called_once_with(self.notify_config.whatsapp_account_sid, self.notify_config.whatsapp_auth_token)
        bot_instance.messages.create.assert_called_once_with(
            body=self.notify.text,
            from_=f'whatsapp:{self.notify_config.whatsapp_sender}',
            to=f'whatsapp:{self.notify.phone}',
        )

        assert self.notify.state == STATE.DELIVERED
        assert self.notify.sent_at == now_time

    @patch('garpix_notify.clients.whatsapp_client.Client')
    def test_send_failed(self, bot_mock: Mock, setup: None):
        response = MagicMock()
        type(response).sid = PropertyMock(return_value=False)
        bot_instance = MagicMock()
        bot_instance.messages.create = MagicMock()
        bot_instance.messages.create.return_value = response
        bot_mock.return_value = bot_instance

        WhatsAppClient.send_whatsapp(self.notify)

        bot_mock.assert_called_once_with(self.notify_config.whatsapp_account_sid, self.notify_config.whatsapp_auth_token)
        bot_instance.messages.create.assert_called_once_with(
            body=self.notify.text,
            from_=f'whatsapp:{self.notify_config.whatsapp_sender}',
            to=f'whatsapp:{self.notify.phone}',
        )

        assert self.notify.state == STATE.REJECTED
        assert NotifyErrorLog.objects.filter(notify=self.notify, error='REJECTED WITH DATA, please test it.').exists()

    @patch('garpix_notify.clients.whatsapp_client.Client')
    def test_send_failed_with_exception(self, bot_mock: Mock, setup: None):
        bot_instance = MagicMock()
        bot_instance.messages.create = MagicMock()
        bot_instance.messages.create.side_effect = Exception('test')
        bot_mock.return_value = bot_instance

        WhatsAppClient.send_whatsapp(self.notify)

        bot_mock.assert_called_once_with(self.notify_config.whatsapp_account_sid, self.notify_config.whatsapp_auth_token)
        bot_instance.messages.create.assert_called_once_with(
            body=self.notify.text,
            from_=f'whatsapp:{self.notify_config.whatsapp_sender}',
            to=f'whatsapp:{self.notify.phone}',
        )

        assert self.notify.state == STATE.REJECTED
        assert NotifyErrorLog.objects.filter(notify=self.notify, error='test').exists()
