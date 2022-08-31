import pytest
from django.conf import settings

from garpix_notify.tests.utils.common_class import CommonTestClass
from garpix_notify.tests.utils.generate_data import (
    generate_templates_views, generate_compiled_email_views, generate_users, generate_category
)
from garpix_notify.models import Notify


@pytest.mark.urls('app.urls')
@pytest.mark.django_db
class TestViews(CommonTestClass):

    @pytest.fixture
    def setup(self):
        self.event = int(getattr(settings, 'REGISTRATION_EVENT', '1'))
        # Тестовый пользователь
        self.data_user = generate_users(3)[2]
        self.user = self.create_user(self.data_user)

        # Генерация данных для создания шаблонов и данных для теста
        self.data_category = generate_category()[0]
        self.data_template_email = generate_templates_views(self.event)[0]
        self.data_compiled_email = generate_compiled_email_views(self.event)[0]

        # Создание шаблонов/категории
        self.category = self.create_category(self.data_category)
        self.template = self.create_template(self.data_template_email, self.category)

    def test_view_endpoint(self, setup, client):
        client.force_login(self.user)
        request = client.get('/')

        assert request.status_code == 201

        notify = Notify.objects.get(event=self.event)

        assert notify.subject == self.data_compiled_email['subject']
        assert notify.html == self.data_compiled_email['html']
        assert notify.email == self.data_compiled_email['email']
        assert notify.type == self.data_compiled_email['type']
        assert notify.event == self.data_compiled_email['event']
