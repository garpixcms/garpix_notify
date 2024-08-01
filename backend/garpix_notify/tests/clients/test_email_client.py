import datetime
import pytest
from unittest.mock import Mock, MagicMock, patch
from garpix_notify.models import Notify, NotifyConfig, NotifyErrorLog, SMTPAccount
from garpix_notify.models.choices import STATE
from garpix_notify.clients import EmailClient
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

        self.notify = Notify.send(event=self.PASS_TEST_EVENT, context={}, user=self.user)[0]
        self.notify_config = NotifyConfig.get_solo()

    def test_send_disabled_via_config(self, setup: None):
        self.notify_config.is_email_enabled = False
        self.notify_config.save()

        EmailClient.send_email(self.notify)

        assert self.notify.state == STATE.DISABLED
        assert NotifyErrorLog.objects.filter(notify=self.notify, error='Not sent (sending is prohibited by settings)').exists()

    def test_send_disabled_without_free_smtp_account(self, setup: None):
        EmailClient.send_email(self.notify)

        assert self.notify.state == STATE.DISABLED
        assert NotifyErrorLog.objects.filter(notify=self.notify, error='No SMTPAccount').exists()


    @patch('garpix_notify.clients.email_client.now')
    @patch('garpix_notify.clients.email_client.SMTP_SSL')
    def test_send_successfull_ssl(self, smtp_ssl: Mock, now_mock: Mock, setup: None):
        now_time = datetime.datetime(2024, 7, 30, 12, 0, 0)
        now_mock.return_value = now_time
        smtp_instance = MagicMock()
        smtp_ssl.return_value = smtp_instance

        account = SMTPAccount.objects.create(
            category=self.category_1,
            host='host',
            port=2222,
            username='user',
            password='user',
            sender='from@mail.ru',
            timeout=10,
            is_use_ssl=True,
            is_use_tls=False,
        )

        EmailClient.send_email(self.notify)

        smtp_ssl.assert_called_once_with(account.host, account.port, timeout=account.timeout)
        smtp_instance.ehlo.assert_called_once()
        smtp_instance.login.assert_called_once_with(account.username, account.password)
        smtp_instance.sendmail.assert_called_once()
        smtp_instance.close.assert_called_once()
        assert self.notify.state == STATE.DELIVERED
        assert self.notify.sent_at == now_time

    @patch('garpix_notify.clients.email_client.now')
    @patch('garpix_notify.clients.email_client.SMTP')
    def test_send_successfull_tls(self, smtp: Mock, now_mock: Mock, setup: None):
        now_time = datetime.datetime(2024, 7, 30, 12, 0, 0)
        now_mock.return_value = now_time
        smtp_instance = MagicMock()
        smtp.return_value = smtp_instance

        account = SMTPAccount.objects.create(
            category=self.category_1,
            host='host',
            port=2222,
            username='user',
            password='user',
            sender='sender',
            timeout=10,
            is_use_ssl=False,
            is_use_tls=True,
        )

        EmailClient.send_email(self.notify)

        smtp.assert_called_once_with(account.host, account.port, timeout=account.timeout)
        smtp_instance.ehlo.assert_called_once()
        smtp_instance.starttls.assert_called_once()
        smtp_instance.login.assert_called_once_with(account.username, account.password)
        smtp_instance.sendmail.assert_called_once()
        smtp_instance.close.assert_called_once()
        assert self.notify.state == STATE.DELIVERED
        assert self.notify.sent_at == now_time

    @patch('garpix_notify.clients.email_client.now')
    @patch('garpix_notify.clients.email_client.SMTP')
    def test_send_failed(self, smtp: Mock, now_mock: Mock, setup: None):
        now_time = datetime.datetime(2024, 7, 30, 12, 0, 0)
        now_mock.return_value = now_time
        smtp_instance = MagicMock()
        smtp.return_value = smtp_instance

        account = SMTPAccount.objects.create(
            category=self.category_1,
            host='host',
            port=2222,
            username='user',
            password='user',
            sender='sender',
            timeout=10,
            is_use_ssl=False,
            is_use_tls=True,
        )
        smtp.side_effect = Exception('Failed to connect')

        EmailClient.send_email(self.notify)

        smtp.assert_called_once_with(account.host, account.port, timeout=account.timeout)

        assert self.notify.state == STATE.REJECTED
        assert NotifyErrorLog.objects.filter(notify=self.notify, error='Failed to connect').exists()
