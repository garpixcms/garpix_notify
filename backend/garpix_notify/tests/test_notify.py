import pytest

from garpix_notify.models import Notify
from .utils.generate_data import (
    generate_users, generate_category, generate_templates, generate_compiled_email, generate_notify_data,
    generate_viber_user, generate_compiled_viber, generate_templates_viber
)
from .utils.common_class import CommonTestClass


@pytest.mark.django_db
class TestNotify(CommonTestClass):

    @pytest.fixture
    def setup(self):
        # Эвенты для теста
        self.PASS_TEST_EVENT = 0
        self.PASS_TEST_EVENT_1 = 1
        self.PASS_TEST_EVENT_2 = 2
        # Тестовый пользователь
        self.data_user = generate_users(3)[2]
        self.data_viber_user = generate_viber_user(2)[1]
        self.user_1 = self.create_user(self.data_user)
        self.user_viber = self.create_user(self.data_viber_user)

        # Общие данные
        self.user_list = self.create_user_list()
        self.data_category = generate_category()[0]
        self.viber_chat_id = 'm4FsaRu5kBi8HzSAC0liFQ=='
        self.test_data = generate_notify_data(self.user_1)

        # Генерация данных для создания шаблонов и данных для теста
        self.data_template_email = generate_templates(self.PASS_TEST_EVENT)[0]
        self.data_compiled_email = generate_compiled_email(self.data_user, self.PASS_TEST_EVENT)[0]

        self.data_template_email_2 = generate_templates(self.PASS_TEST_EVENT_1)[0]
        self.data_compiled_email_2 = generate_compiled_email(self.data_user, self.PASS_TEST_EVENT_1)[0]

        self.data_template_viber = generate_templates_viber(self.PASS_TEST_EVENT_2)[0]
        self.data_compiled_viber = generate_compiled_viber(self.viber_chat_id, self.PASS_TEST_EVENT_2)[0]

        # Создание шаблонов/категорий
        self.category_1 = self.create_category(self.data_category)
        self.template_1 = self.create_template(self.data_template_email, self.category_1)
        self.template_2 = self.create_template(self.data_template_email_2, self.category_1, self.user_list)
        self.template_viber = self.create_template(self.data_template_viber, self.category_1, self.user_list)

    def test_notify_email_positive(self, setup):
        # Сверяем корректно ли создались объекты
        assert self.category_1.title == self.data_category['title']
        assert self.category_1.template == self.data_category['template']
        assert self.template_1.title == self.data_template_email['title']
        assert self.template_1.subject, self.data_template_email['subject']
        assert self.template_1.text == self.data_template_email['text']
        assert self.template_1.html == self.data_template_email['html']
        assert self.template_1.type == self.data_template_email['type']
        assert self.template_1.event == self.data_template_email['event']

        # Создаем письмо
        notify = Notify.send(event=self.PASS_TEST_EVENT, context=self.test_data, user=self.user_1)

        # Сверяем с шаблоном и ожидаемым результатом
        assert notify[0].event == self.template_1.event
        assert notify[0].subject == self.data_compiled_email['subject']
        assert notify[0].text == self.data_compiled_email['text']
        assert notify[0].html == self.data_compiled_email['html']
        assert notify[0].type == self.data_compiled_email['type']
        assert notify[0].event == self.data_compiled_email['event']

    def test_notify_email_user_list(self, setup):
        # Сверяем корректно ли создались объекты
        assert self.template_2.title == self.data_template_email_2['title']
        assert self.template_2.subject, self.data_template_email_2['subject']
        assert self.template_2.text == self.data_template_email_2['text']
        assert self.template_2.html == self.data_template_email_2['html']
        assert self.template_2.type == self.data_template_email_2['type']
        assert self.template_2.event == self.data_template_email_2['event']
        assert self.template_2.category.id == self.category_1.id

        # Создаем письмо
        notify = Notify.send(event=self.PASS_TEST_EVENT_1, context=self.test_data, user=self.user_1)

        # Сверяем с шаблоном и ожидаемым результатом
        assert notify[0].event == self.template_2.event
        assert notify[0].email == self.user_1.email
        assert notify[0].subject == self.data_compiled_email_2['subject']
        assert notify[0].text == self.data_compiled_email_2['text']
        assert notify[0].html == self.data_compiled_email_2['html']
        assert notify[0].type == self.data_compiled_email_2['type']
        assert notify[0].event == self.data_compiled_email_2['event']

    def test_notify_viber(self, setup):
        # Сверяем корректно ли создались объекты
        assert self.template_viber.title == self.data_template_viber['title']
        assert self.template_viber.subject, self.data_template_viber['subject']
        assert self.template_viber.text == self.data_template_viber['text']
        assert self.template_viber.html == self.data_template_viber['html']
        assert self.template_viber.type == self.data_template_viber['type']
        assert self.template_viber.event == self.data_template_viber['event']
        assert self.template_viber.category.id == self.category_1.id

        # Создаем письмо
        notify = Notify.send(event=self.PASS_TEST_EVENT_2, context=self.test_data, user=self.user_viber)

        # Сверяем с шаблоном и ожидаемым результатом
        assert notify[0].event == self.template_viber.event
        assert notify[0].email == self.user_viber.email
        assert notify[0].subject == self.data_compiled_viber['subject']
        assert notify[0].text == self.data_compiled_viber['text']
        assert notify[0].html == self.data_compiled_viber['html']
        assert notify[0].type == self.data_compiled_viber['type']
        assert notify[0].event == self.data_compiled_viber['event']
        assert notify[0].user.viber_chat_id == self.viber_chat_id
