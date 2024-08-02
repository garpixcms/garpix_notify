import datetime
import pytest
from unittest.mock import Mock, patch
from garpix_notify.models import Notify, NotifyConfig, NotifyErrorLog
from garpix_notify.models.choices import SMS_URL, STATE
from garpix_notify.clients import SMSClient
from ..utils.common_class import CommonTestClass
from ..utils.generate_data import (
    generate_users, generate_category, generate_system_template_data,
)


@pytest.mark.django_db
class TestSMSClient(CommonTestClass):
    @pytest.fixture
    def setup(self):
        # Tests Events
        self.PASS_TEST_EVENT = 1

        # Users data
        self.user = self.create_user(generate_users(1)[0])
        self.user_list = self.create_system_user_list()

        # Data for test user
        self.data_category = generate_category()[0]

        self.data_template = generate_system_template_data('text message', self.PASS_TEST_EVENT)[0]

        # Creating templates/category
        self.category_1 = self.create_category(self.data_category)
        self.template_1 = self.create_template(self.data_template, self.category_1)

        self.notify = Notify.send(event=self.PASS_TEST_EVENT, context={}, user=self.user, phone='+79998887766')[0]
        self.notify_config = NotifyConfig.get_solo()

    def test_sms_disabled_via_config(self, setup: None):
        self.notify_config.is_sms_enabled = False
        self.notify_config.save()

        SMSClient.send_sms(self.notify)

        assert self.notify.state == STATE.DISABLED
        assert NotifyErrorLog.objects.filter(notify=self.notify, error='Not sent (sending is prohibited by settings)').exists()

    @patch('garpix_notify.clients.sms_client.now')
    @patch('garpix_notify.clients.sms_client.requests')
    def test_sms_successfull_smsru_api(self, requests: Mock, now_mock: Mock, setup: None):
        now_time = datetime.datetime(2024, 7, 30, 12, 0, 0)
        now_mock.return_value = now_time
        self.notify_config.sms_url_type = SMS_URL.SMSRU_ID
        self.notify_config.sms_api_id = 'test-api'
        self.notify_config.save()

        expected_response = {
            'status': 'OK',
            'status_code': 2,
            'balance': 3,
            'sms': {
                '79998887766': {
                    "status": "OK",
                    "status_code": 1,
                    "status_text": "Done",
                }
            }
        }
        response = Mock()
        response.json = Mock(return_value=expected_response)
        requests.get.return_value = response

        SMSClient.send_sms(self.notify)

        requests.get.assert_called_once_with(f'{SMS_URL.SMSRU_URL}?api_id=test-api&to=+79998887766&msg=text+message&json=1')
        response.json.assert_called_once()

        assert self.notify.state == STATE.DELIVERED
        assert self.notify.sent_at == now_time
        assert NotifyErrorLog.objects.filter(notify=self.notify, error='Статус основного запроса: OK, Код статуса: 2, Баланс: 3').exists()

    @patch('garpix_notify.clients.sms_client.requests')
    def test_sms_failed_smsru_api(self, requests: Mock, setup: None):
        self.notify_config.sms_url_type = SMS_URL.SMSRU_ID
        self.notify_config.sms_api_id = 'test-api'
        self.notify_config.save()

        expected_response = {
            'status': 'Not OK',
            'status_code': -2,
            'status_text': 'Error',
        }
        response = Mock()
        response.json = Mock(return_value=expected_response)
        requests.get.return_value = response

        SMSClient.send_sms(self.notify)

        requests.get.assert_called_once_with(f'{SMS_URL.SMSRU_URL}?api_id=test-api&to=+79998887766&msg=text+message&json=1')
        response.json.assert_called_once()

        assert self.notify.state == STATE.REJECTED
        assert self.notify.sent_at is None
        assert NotifyErrorLog.objects.filter(notify=self.notify, error='Статус: Not OK, Код статуса: -2, Описание ошибки: Error').exists()

    @patch('garpix_notify.clients.sms_client.now')
    @patch('garpix_notify.clients.sms_client.requests')
    def test_sms_failed_client_smsru_api(self, requests: Mock, now_mock: Mock, setup: None):
        now_time = datetime.datetime(2024, 7, 30, 12, 0, 0)
        now_mock.return_value = now_time
        self.notify_config.sms_url_type = SMS_URL.SMSRU_ID
        self.notify_config.sms_api_id = 'test-api'
        self.notify_config.save()

        expected_response = {
            'status': 'OK',
            'status_code': 2,
            'balance': 3,
            'sms': {
                '79998887766': {
                    "status": "ERROR",
                    "status_code": -1,
                    "status_text": "Err",
                }
            }
        }
        response = Mock()
        response.json = Mock(return_value=expected_response)
        requests.get.return_value = response

        SMSClient.send_sms(self.notify)

        requests.get.assert_called_once_with(f'{SMS_URL.SMSRU_URL}?api_id=test-api&to=+79998887766&msg=text+message&json=1')
        response.json.assert_called_once()

        assert self.notify.state == STATE.DELIVERED
        assert self.notify.sent_at == now_time
        assert NotifyErrorLog.objects.filter(notify=self.notify, error='Статус основного запроса: OK, Код статуса: 2, Баланс: 3').exists()
        assert NotifyErrorLog.objects.filter(notify=self.notify, error='Ошибка у абонента: Номер: 79998887766, Статус: ERROR, Код статуса: -1, Описание: Err').exists()

    @patch('garpix_notify.clients.sms_client.now')
    @patch('garpix_notify.clients.sms_client.requests')
    def test_sms_successfull_webszk(self, requests: Mock, now_mock: Mock, setup: None):
        now_time = datetime.datetime(2024, 7, 30, 12, 0, 0)
        now_mock.return_value = now_time
        self.notify_config.sms_url_type = SMS_URL.WEBSZK_ID
        self.notify_config.sms_from = '111'
        self.notify_config.sms_login = 'test-login'
        self.notify_config.sms_password = 'test-password'
        self.notify_config.save()

        expected_response = [1, 2, 3]
        response = Mock()
        response.json = Mock(return_value=expected_response)
        requests.get.return_value = response

        SMSClient.send_sms(self.notify)

        requests.get.assert_called_once_with(f'{SMS_URL.WEBSZK_URL}?login=test-login&pass=test-password&sourceAddress=111&destinationAddress=+79998887766&data=text+message')
        response.json.assert_called_once()

        assert self.notify.state == STATE.DELIVERED
        assert self.notify.sent_at == now_time
        assert NotifyErrorLog.objects.filter(notify=self.notify, error='Статус операции: Успешно, ID отправленных сообщений: [1, 2, 3]').exists()

    @patch('garpix_notify.clients.sms_client.requests')
    def test_sms_failed_webszk(self, requests: Mock, setup: None):
        self.notify_config.sms_url_type = SMS_URL.WEBSZK_ID
        self.notify_config.sms_from = '111'
        self.notify_config.sms_login = 'test-login'
        self.notify_config.sms_password = 'test-password'
        self.notify_config.save()

        expected_response = {
            'Code': 'Not OK',
        }
        response = Mock()
        response.json = Mock(return_value=expected_response)
        requests.get.return_value = response

        SMSClient.send_sms(self.notify)

        requests.get.assert_called_once_with(f'{SMS_URL.WEBSZK_URL}?login=test-login&pass=test-password&sourceAddress=111&destinationAddress=+79998887766&data=text+message')
        response.json.assert_called_once()

        assert self.notify.state == STATE.REJECTED
        assert self.notify.sent_at is None
        assert NotifyErrorLog.objects.filter(notify=self.notify, error="Статус операции: {'Code': 'Not OK'}").exists()

    @patch('garpix_notify.clients.sms_client.now')
    @patch('garpix_notify.clients.sms_client.requests')
    def test_sms_successfull_iq(self, requests: Mock, now_mock: Mock, setup: None):
        now_time = datetime.datetime(2024, 7, 30, 12, 0, 0)
        now_mock.return_value = now_time
        self.notify_config.sms_url_type = SMS_URL.IQSMS_ID
        self.notify_config.sms_from = '111'
        self.notify_config.sms_login = 'test-login'
        self.notify_config.sms_password = 'test-password'
        self.notify_config.save()

        expected_response = {
            'status': 'ok',
            'code': 2,
            'description': 'Done',
        }
        response = Mock()
        response.json = Mock(return_value=expected_response)
        requests.get.return_value = response

        SMSClient.send_sms(self.notify)

        requests.get.assert_called_once_with(f'{SMS_URL.IQSMS_URL}?login=test-login&password=test-password&phone=+79998887766&text=text+message')
        response.json.assert_called_once()

        assert self.notify.state == STATE.DELIVERED
        assert self.notify.sent_at == now_time
        assert NotifyErrorLog.objects.filter(notify=self.notify, error='Статус: ok, Код статуса: 2, Описание: Done').exists()

    @patch('garpix_notify.clients.sms_client.requests')
    def test_sms_failed_iq(self, requests: Mock, setup: None):
        self.notify_config.sms_url_type = SMS_URL.IQSMS_ID
        self.notify_config.sms_from = '111'
        self.notify_config.sms_login = 'test-login'
        self.notify_config.sms_password = 'test-password'
        self.notify_config.save()

        expected_response = {
            'status': 'Not OK',
            'code': -1,
            'description': 'Fail',
        }
        response = Mock()
        response.json = Mock(return_value=expected_response)
        requests.get.return_value = response

        SMSClient.send_sms(self.notify)

        requests.get.assert_called_once_with(f'{SMS_URL.IQSMS_URL}?login=test-login&password=test-password&phone=+79998887766&text=text+message')
        response.json.assert_called_once()

        assert self.notify.state == STATE.REJECTED
        assert self.notify.sent_at is None
        assert NotifyErrorLog.objects.filter(notify=self.notify, error='Статус: Not OK, Код статуса: -1, Описание ошибки: Fail').exists()

    @patch('garpix_notify.clients.sms_client.now')
    @patch('garpix_notify.clients.sms_client.requests')
    def test_sms_successfull_infosms(self, requests: Mock, now_mock: Mock, setup: None):
        now_time = datetime.datetime(2024, 7, 30, 12, 0, 0)
        now_mock.return_value = now_time
        self.notify_config.sms_url_type = SMS_URL.INFOSMS_ID
        self.notify_config.sms_from = '111'
        self.notify_config.sms_login = 'test-login'
        self.notify_config.sms_password = 'test-password'
        self.notify_config.save()

        SMSClient.send_sms(self.notify)

        requests.get.assert_called_once_with(f'{SMS_URL.INFOSMS_URL}?login=test-login&pwd=test-password&sender=111&phones=+79998887766&message=text+message')

        assert self.notify.state == STATE.DELIVERED
        assert self.notify.sent_at == now_time
        assert not NotifyErrorLog.objects.filter(notify=self.notify).exists()

    @patch('garpix_notify.clients.sms_client.now')
    @patch('garpix_notify.clients.sms_client.requests')
    def test_sms_successfull_smscentre(self, requests: Mock, now_mock: Mock, setup: None):
        now_time = datetime.datetime(2024, 7, 30, 12, 0, 0)
        now_mock.return_value = now_time
        self.notify_config.sms_url_type = SMS_URL.SMSCENTRE_ID
        self.notify_config.sms_from = '111'
        self.notify_config.sms_login = 'test-login'
        self.notify_config.sms_password = 'test-password'
        self.notify_config.save()

        SMSClient.send_sms(self.notify)

        requests.get.assert_called_once_with(f'{SMS_URL.SMSCENTRE_URL}?login=test-login&psw=test-password&phones=+79998887766&mes=text+message')

        assert self.notify.state == STATE.DELIVERED
        assert self.notify.sent_at == now_time
        assert not NotifyErrorLog.objects.filter(notify=self.notify).exists()

    @patch('garpix_notify.clients.sms_client.now')
    @patch('garpix_notify.clients.sms_client.requests')
    def test_sms_successfull_sms_prosto(self, requests: Mock, now_mock: Mock, setup: None):
        now_time = datetime.datetime(2024, 7, 30, 12, 0, 0)
        now_mock.return_value = now_time
        self.notify_config.sms_url_type = SMS_URL.SMS_PROSTO_ID
        self.notify_config.sms_from = '111'
        self.notify_config.sms_login = 'test-login'
        self.notify_config.sms_password = 'test-password'
        self.notify_config.save()

        expected_response = {
            'code': 1,
            'descr': 'Done',
        }
        response = Mock()
        response.json = Mock(return_value=expected_response)
        requests.get.return_value = response

        SMSClient.send_sms(self.notify)

        requests.get.assert_called_once_with(f'{SMS_URL.SMS_PROSTO_URL}?login=test-login&password=test-password&txt=text+message&to=+79998887766')
        response.json.assert_called_once()

        assert self.notify.state == STATE.DELIVERED
        assert self.notify.sent_at == now_time
        assert NotifyErrorLog.objects.filter(notify=self.notify, error='Статус: 1, Описание: Done').exists()

    @patch('garpix_notify.clients.sms_client.requests')
    def test_sms_failed_sms_prosto(self, requests: Mock, setup: None):
        self.notify_config.sms_url_type = SMS_URL.SMS_PROSTO_ID
        self.notify_config.sms_from = '111'
        self.notify_config.sms_login = 'test-login'
        self.notify_config.sms_password = 'test-password'
        self.notify_config.save()

        expected_response = {
            'code': 0,
            'descr': 'Fail',
        }
        response = Mock()
        response.json = Mock(return_value=expected_response)
        requests.get.return_value = response

        SMSClient.send_sms(self.notify)

        requests.get.assert_called_once_with(f'{SMS_URL.SMS_PROSTO_URL}?login=test-login&password=test-password&txt=text+message&to=+79998887766')
        response.json.assert_called_once()

        assert self.notify.state == STATE.REJECTED
        assert self.notify.sent_at is None
        assert NotifyErrorLog.objects.filter(notify=self.notify, error='Статус: 0, Описание ошибки: Fail').exists()

    @patch('garpix_notify.clients.sms_client.now')
    @patch('garpix_notify.clients.sms_client.requests')
    def test_sms_successfull_sms_prosto(self, requests: Mock, now_mock: Mock, setup: None):
        now_time = datetime.datetime(2024, 7, 30, 12, 0, 0)
        now_mock.return_value = now_time
        self.notify_config.sms_url_type = SMS_URL.SMS_PROSTO_ID
        self.notify_config.sms_from = '111'
        self.notify_config.sms_api_id = '222'
        self.notify_config.sms_login = 'test-login'
        self.notify_config.sms_password = 'test-password'
        self.notify_config.save()

        expected_response = {
            'response': {
                'msg': {
                    'err_code': 0,
                    'text': 'Done',
                }
            }
        }
        response = Mock()
        response.json = Mock(return_value=expected_response)
        requests.get.return_value = response

        SMSClient.send_sms(self.notify)

        requests.get.assert_called_once_with(f'{SMS_URL.SMS_PROSTO_URL}?login=test-login&password=test-password&method=push_msg&format=json&sender_name=111&text=text+message&phone=+79998887766&key=222')
        response.json.assert_called_once()

        assert self.notify.state == STATE.DELIVERED
        assert self.notify.sent_at == now_time
        assert NotifyErrorLog.objects.filter(notify=self.notify, error='Статус: 0, Описание: Done').exists()

    @patch('garpix_notify.clients.sms_client.requests')
    def test_sms_failed_sms_prosto(self, requests: Mock, setup: None):
        self.notify_config.sms_url_type = SMS_URL.SMS_PROSTO_ID
        self.notify_config.sms_from = '111'
        self.notify_config.sms_api_id = '222'
        self.notify_config.sms_login = 'test-login'
        self.notify_config.sms_password = 'test-password'
        self.notify_config.save()

        expected_response = {
            'response': {
                'msg': {
                    'err_code': -1,
                    'text': 'Fail',
                }
            }
        }
        response = Mock()
        response.json = Mock(return_value=expected_response)
        requests.get.return_value = response

        SMSClient.send_sms(self.notify)

        requests.get.assert_called_once_with(f'{SMS_URL.SMS_PROSTO_URL}?login=test-login&password=test-password&method=push_msg&format=json&sender_name=111&text=text+message&phone=+79998887766&key=222')
        response.json.assert_called_once()

        assert self.notify.state == STATE.REJECTED
        assert self.notify.sent_at is None
        assert NotifyErrorLog.objects.filter(notify=self.notify, error='Статус: -1, Описание ошибки: Fail').exists()
