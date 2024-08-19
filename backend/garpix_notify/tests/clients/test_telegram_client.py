import datetime
import pytest
import telegram
from unittest.mock import Mock, MagicMock, patch
from garpix_notify.models import Notify, NotifyConfig, NotifyErrorLog
from garpix_notify.models.choices import STATE, PARSE_MODE_TELEGRAM
from garpix_notify.clients import TelegramClient
from ..utils.common_class import CommonTestClass
from ..utils.generate_data import (
    generate_users, generate_category, generate_system_notify_data, generate_system_template_data,
)


@pytest.mark.django_db
class TestTelegramClient(CommonTestClass):
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
        self.notify_config.telegram_api_key = 'test'
        self.notify_config.telegram_parse_mode = PARSE_MODE_TELEGRAM.MARKDOWN
        self.notify_config.save()

    def test_send_disabled_via_config(self, setup: None):
        self.notify_config.is_telegram_enabled = False
        self.notify_config.save()

        TelegramClient.send_telegram(self.notify)

        assert self.notify.state == STATE.DISABLED
        assert NotifyErrorLog.objects.filter(notify=self.notify, error='Not sent (sending is prohibited by settings)').exists()

    @patch('garpix_notify.clients.telegram_client.now')
    @patch('telegram.Bot')
    def test_send_successfull(self, bot_mock: Mock, now_mock: Mock, setup: None):
        now_time = datetime.datetime(2024, 7, 30, 12, 0, 0)
        now_mock.return_value = now_time
        bot_instance = MagicMock()
        bot_instance.sendMessage = MagicMock()
        bot_instance.sendMessage.return_value = True
        bot_mock.return_value = bot_instance

        TelegramClient.send_telegram(self.notify)

        bot_mock.assert_called_once_with(token=self.notify_config.telegram_api_key)
        bot_instance.sendMessage.assert_called_once_with(
            chat_id=self.notify.telegram_chat_id,
            text=self.notify.text,
            parse_mode=self.notify_config.telegram_parse_mode,
            disable_web_page_preview=self.notify_config.telegram_disable_web_page_preview,
            disable_notification=self.notify_config.telegram_disable_notification,
            timeout=self.notify_config.telegram_timeout,
            allow_sending_without_reply=self.notify_config.telegram_allow_sending_without_reply
        )

        assert self.notify.state == STATE.DELIVERED
        assert self.notify.sent_at == now_time

    @patch('telegram.Bot')
    def test_send_failed(self, bot_mock: Mock, setup: None):
        bot_instance = MagicMock()
        bot_instance.sendMessage = MagicMock()
        bot_instance.sendMessage.return_value = False
        bot_mock.return_value = bot_instance

        TelegramClient.send_telegram(self.notify)

        bot_mock.assert_called_once_with(token=self.notify_config.telegram_api_key)
        bot_instance.sendMessage.assert_called_once_with(
            chat_id=self.notify.telegram_chat_id,
            text=self.notify.text,
            parse_mode=self.notify_config.telegram_parse_mode,
            disable_web_page_preview=self.notify_config.telegram_disable_web_page_preview,
            disable_notification=self.notify_config.telegram_disable_notification,
            timeout=self.notify_config.telegram_timeout,
            allow_sending_without_reply=self.notify_config.telegram_allow_sending_without_reply
        )

        assert self.notify.state == STATE.REJECTED
        assert NotifyErrorLog.objects.filter(notify=self.notify, error='REJECTED WITH DATA, please test it.').exists()

    @patch('telegram.Bot')
    def test_send_failed_with_exception(self, bot_mock: Mock, setup: None):
        bot_instance = MagicMock()
        bot_instance.sendMessage = MagicMock()
        bot_instance.sendMessage.side_effect = telegram.error.ChatMigrated(10)
        bot_instance.sendMessage.return_value = False
        bot_mock.return_value = bot_instance

        TelegramClient.send_telegram(self.notify)

        bot_mock.assert_called_once_with(token=self.notify_config.telegram_api_key)
        bot_instance.sendMessage.assert_called_once_with(
            chat_id=self.notify.telegram_chat_id,
            text=self.notify.text,
            parse_mode=self.notify_config.telegram_parse_mode,
            disable_web_page_preview=self.notify_config.telegram_disable_web_page_preview,
            disable_notification=self.notify_config.telegram_disable_notification,
            timeout=self.notify_config.telegram_timeout,
            allow_sending_without_reply=self.notify_config.telegram_allow_sending_without_reply
        )

        assert self.notify.state == STATE.REJECTED
        assert NotifyErrorLog.objects.filter(notify=self.notify, error='Group migrated to supergroup. New chat id: 10').exists()
