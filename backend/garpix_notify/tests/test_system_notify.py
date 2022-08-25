import pytest

from garpix_notify.models import SystemNotify
from .utils.common_class import CommonTestClass
from .utils.generate_data import (
    generate_users, generate_category, generate_system_notify_data, generate_system_template_data,
    generate_compiled_system
)


@pytest.mark.django_db
class TestSystemNotify(CommonTestClass):

    @pytest.fixture
    def setup(self):
        # Tests Events
        self.PASS_TEST_EVENT = 1
        self.PASS_TEST_EVENT_1 = 2

        # Users data
        self.data_user = generate_users(1)[0]
        self.user_list = self.create_system_user_list()
        self.user_1 = self.create_user(self.data_user)

        # Data for test user
        self.some_data_dict = generate_system_notify_data()
        self.data_category = generate_category()[0]

        self.data_template_system_1 = generate_system_template_data(self.some_data_dict, self.PASS_TEST_EVENT)[0]
        self.data_compiled_system_1 = generate_compiled_system(self.some_data_dict, self.PASS_TEST_EVENT, self.user_1)[0]

        self.data_template_email_2 = generate_system_template_data(self.some_data_dict, self.PASS_TEST_EVENT_1)[0]

        # Creating templates/category
        self.category_1 = self.create_category(self.data_category)
        self.template_1 = self.create_template(self.data_template_system_1, self.category_1)
        self.template_2 = self.create_template(self.data_template_email_2, self.category_1, self.user_list)

    def test_system_notify_positive(self, setup):
        assert self.category_1.title == self.data_category['title']
        assert self.category_1.template == self.data_category['template']
        assert self.template_1.title == self.data_template_system_1['title']
        assert self.template_1.subject, self.data_template_system_1['subject']
        assert self.template_1.text == self.data_template_system_1['text']
        assert self.template_1.html == self.data_template_system_1['html']
        assert self.template_1.type == self.data_template_system_1['type']
        assert self.template_1.event == self.data_template_system_1['event']

        # Create system notify
        SystemNotify.send(
            self.some_data_dict, user=self.user_1, event=self.PASS_TEST_EVENT
        )
        notify = SystemNotify.objects.filter(user=self.user_1, event=self.PASS_TEST_EVENT).first()

        assert notify.event == self.template_1.event
        assert notify.title == self.data_compiled_system_1['title']
        assert notify.data_json == self.data_compiled_system_1['data_json']
        assert notify.type == self.data_compiled_system_1['type']
        assert notify.event == self.data_compiled_system_1['event']

    def test_system_notify_user_list(self, setup):
        assert self.category_1.title == self.data_category['title']
        assert self.category_1.template == self.data_category['template']
        assert self.template_1.title == self.data_template_system_1['title']
        assert self.template_1.subject, self.data_template_system_1['subject']
        assert self.template_1.text == self.data_template_system_1['text']
        assert self.template_1.html == self.data_template_system_1['html']
        assert self.template_1.type == self.data_template_system_1['type']
        assert self.template_1.event == self.data_template_system_1['event']

        # Create system notify
        SystemNotify.send(self.some_data_dict, event=self.PASS_TEST_EVENT_1)
        notify_qs = SystemNotify.objects.filter(event=self.PASS_TEST_EVENT_1)

        for notify in notify_qs:
            self.data_compiled_system_2 = (
                generate_compiled_system(self.some_data_dict, self.PASS_TEST_EVENT_1, notify.user)[0]
            )

            assert notify.event == self.template_2.event
            assert notify.title == self.data_compiled_system_2['title']
            assert notify.data_json == self.data_compiled_system_2['data_json']
            assert notify.type == self.data_compiled_system_2['type']
            assert notify.event == self.data_compiled_system_2['event']
