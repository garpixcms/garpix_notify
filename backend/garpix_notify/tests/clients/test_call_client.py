import datetime
import pytest
from unittest.mock import Mock, patch
from garpix_notify.models import Notify, NotifyConfig, NotifyErrorLog
from garpix_notify.models.choices import CALL_URL, STATE
from garpix_notify.clients import CallClient
from ..utils.common_class import CommonTestClass
from ..utils.generate_data import (
    generate_users, generate_category, generate_system_notify_data, generate_system_template_data,
)


@pytest.mark.django_db
class TestEmailClient(CommonTestClass):
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

        self.notify = Notify.send(event=self.PASS_TEST_EVENT, context={}, user=self.user, phone='+79998887766')[0]
        self.notify_config = NotifyConfig.get_solo()

    def test_call_disabled_via_config(self, setup: None):
        self.notify_config.is_call_enabled = False
        self.notify_config.save()

        CallClient.send_call(self.notify)

        assert self.notify.state == STATE.DISABLED
        assert NotifyErrorLog.objects.filter(notify=self.notify, error='Not sent (sending is prohibited by settings)').exists()

    @patch('garpix_notify.clients.call_client.now')
    @patch('garpix_notify.clients.call_client.requests')
    def test_call_successfull_smsru_api(self, requests: Mock, now_mock: Mock, setup: None):
        now_time = datetime.datetime(2024, 7, 30, 12, 0, 0)
        now_mock.return_value = now_time
        self.notify_config.call_url_type = CALL_URL.SMSRU_CALL_API_ID
        self.notify_config.call_api_id = 'test-api'
        self.notify_config.save()

        expected_response = {
            'status': 'OK',
            'code': 2,
            'balance': 3,
            'call_id': 4
        }
        response = Mock()
        response.json = Mock(return_value=expected_response)
        requests.get.return_value = response

        CallClient.send_call(self.notify)

        requests.get.assert_called_once_with(f'{CALL_URL.SMSRU_CALL_URL}?api_id=test-api&phone=+79998887766&json=1')
        response.json.assert_called_once()

        assert self.notify.state == STATE.DELIVERED
        assert self.notify.sent_at == now_time
        assert NotifyErrorLog.objects.filter(notify=self.notify, error='Status: OK, Code: 2, Balance: 3, ID_Call: 4').exists()

    @patch('garpix_notify.clients.call_client.requests')
    def test_call_failed_smsru_api(self, requests: Mock, setup: None):
        self.notify_config.call_url_type = CALL_URL.SMSRU_CALL_API_ID
        self.notify_config.call_api_id = 'test-api'
        self.notify_config.save()

        expected_response = {
            'status': 'Not OK',
            'status_code': -2,
            'status_text': 'Error',
        }
        response = Mock()
        response.json = Mock(return_value=expected_response)
        requests.get.return_value = response

        CallClient.send_call(self.notify)

        requests.get.assert_called_once_with(f'{CALL_URL.SMSRU_CALL_URL}?api_id=test-api&phone=+79998887766&json=1')
        response.json.assert_called_once()

        assert self.notify.state == STATE.REJECTED
        assert self.notify.sent_at is None
        assert NotifyErrorLog.objects.filter(notify=self.notify, error='Status: Not OK, Status_code: -2, Status_text: Error').exists()

    @patch('garpix_notify.clients.call_client.now')
    @patch('garpix_notify.clients.call_client.requests')
    def test_call_successfull_smsru_login(self, requests: Mock, now_mock: Mock, setup: None):
        now_time = datetime.datetime(2024, 7, 30, 12, 0, 0)
        now_mock.return_value = now_time
        self.notify_config.call_url_type = CALL_URL.SMSRU_CALL_ID
        self.notify_config.call_login = 'test-login'
        self.notify_config.call_password = 'test-password'
        self.notify_config.save()

        expected_response = {
            'status': 'OK',
            'code': 2,
            'balance': 3,
            'call_id': 4
        }
        response = Mock()
        response.json = Mock(return_value=expected_response)
        requests.get.return_value = response

        CallClient.send_call(self.notify)

        requests.get.assert_called_once_with(f'{CALL_URL.SMSRU_CALL_URL}?login=test-login&password=test-password&phone=+79998887766&json=1')
        response.json.assert_called_once()

        assert self.notify.state == STATE.DELIVERED
        assert self.notify.sent_at == now_time
        assert NotifyErrorLog.objects.filter(notify=self.notify, error='Status: OK, Code: 2, Balance: 3, ID_Call: 4').exists()

    @patch('garpix_notify.clients.call_client.requests')
    def test_call_failed_smsru_login(self, requests: Mock, setup: None):
        self.notify_config.call_url_type = CALL_URL.SMSRU_CALL_ID
        self.notify_config.call_login = 'test-login'
        self.notify_config.call_password = 'test-password'
        self.notify_config.save()

        expected_response = {
            'status': 'Not OK',
            'status_code': -2,
            'status_text': 'Error',
        }
        response = Mock()
        response.json = Mock(return_value=expected_response)
        requests.get.return_value = response

        CallClient.send_call(self.notify)

        requests.get.assert_called_once_with(f'{CALL_URL.SMSRU_CALL_URL}?login=test-login&password=test-password&phone=+79998887766&json=1')
        response.json.assert_called_once()

        assert self.notify.state == STATE.REJECTED
        assert self.notify.sent_at is None
        assert NotifyErrorLog.objects.filter(notify=self.notify, error='Status: Not OK, Status_code: -2, Status_text: Error').exists()

    @patch('garpix_notify.clients.call_client.now')
    @patch('garpix_notify.clients.call_client.requests')
    def test_call_successfull_smscenter(self, requests: Mock, now_mock: Mock, setup: None):
        now_time = datetime.datetime(2024, 7, 30, 12, 0, 0)
        now_mock.return_value = now_time
        self.notify_config.call_url_type = CALL_URL.SMSCENTRE_ID
        self.notify_config.call_login = 'test-login'
        self.notify_config.call_password = 'test-password'
        self.notify_config.save()

        expected_response = {
            'error': 0,
            'id': 1,
            'code': 2,
            'cnt': 3,
            'balance': 4,
        }
        response = Mock()
        response.json = Mock(return_value=expected_response)
        requests.get.return_value = response

        CallClient.send_call(self.notify)

        requests.get.assert_called_once_with(f'{CALL_URL.SMSCENTRE_URL}?login=test-login&psw=test-password&phones=+79998887766&mes=code&call=1&fmt=3')
        response.json.assert_called_once()

        assert self.notify.state == STATE.DELIVERED
        assert self.notify.sent_at == now_time
        assert NotifyErrorLog.objects.filter(notify=self.notify, error='Status: 1, Code: 2, Balance: 4, ID_Call: 3').exists()

    @patch('garpix_notify.clients.call_client.requests')
    def test_call_failed_smscenter(self, requests: Mock, setup: None):
        self.notify_config.call_url_type = CALL_URL.SMSCENTRE_ID
        self.notify_config.call_login = 'test-login'
        self.notify_config.call_password = 'test-password'
        self.notify_config.save()

        expected_response = {
            'error': 1,
            'status': 'Not OK',
            'error_code': -2,
        }
        response = Mock()
        response.json = Mock(return_value=expected_response)
        requests.get.return_value = response

        CallClient.send_call(self.notify)

        requests.get.assert_called_once_with(f'{CALL_URL.SMSCENTRE_URL}?login=test-login&psw=test-password&phones=+79998887766&mes=code&call=1&fmt=3')
        response.json.assert_called_once()

        assert self.notify.state == STATE.REJECTED
        assert self.notify.sent_at is None
        assert NotifyErrorLog.objects.filter(notify=self.notify, error='Status: Not OK, Status_code: -2, Status_text: 1').exists()

    @patch('garpix_notify.clients.call_client.now')
    @patch('garpix_notify.clients.call_client.requests')
    def test_call_successfull_ucaller(self, requests: Mock, now_mock: Mock, setup: None):
        now_time = datetime.datetime(2024, 7, 30, 12, 0, 0)
        now_mock.return_value = now_time
        self.notify_config.call_url_type = CALL_URL.UCALLER_ID
        self.notify_config.call_login = 'test-login'
        self.notify_config.call_password = 'test-password'
        self.notify_config.save()

        expected_response = {
            'error': 0,
            'status': 1,
            'code': 2,
            'balance': 3,
            'unique_request_id': 4,
        }
        response = Mock()
        response.json = Mock(return_value=expected_response)
        requests.get.return_value = response

        CallClient.send_call(self.notify)

        requests.get.assert_called_once_with(f'{CALL_URL.UCALLER_URL}?key=test-password&service_id=test-login&phone=+79998887766')
        response.json.assert_called_once()

        assert self.notify.state == STATE.DELIVERED
        assert self.notify.sent_at == now_time
        assert NotifyErrorLog.objects.filter(notify=self.notify, error='Status: 1, Code: 2, Balance: 3, ID_Call: 4').exists()

    @patch('garpix_notify.clients.call_client.requests')
    def test_call_failed_ucaller(self, requests: Mock, setup: None):
        self.notify_config.call_url_type = CALL_URL.UCALLER_ID
        self.notify_config.call_login = 'test-login'
        self.notify_config.call_password = 'test-password'
        self.notify_config.save()

        expected_response = {
            'status': 0,
            'code': 1,
            'error': -2,
        }
        response = Mock()
        response.json = Mock(return_value=expected_response)
        requests.get.return_value = response

        CallClient.send_call(self.notify)

        requests.get.assert_called_once_with(f'{CALL_URL.UCALLER_URL}?key=test-password&service_id=test-login&phone=+79998887766')
        response.json.assert_called_once()

        assert self.notify.state == STATE.REJECTED
        assert self.notify.sent_at is None
        assert NotifyErrorLog.objects.filter(notify=self.notify, error='Status: 0, Status_code: 1, Status_text: -2').exists()
