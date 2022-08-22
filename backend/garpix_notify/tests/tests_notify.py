import django
import os

from django.utils.crypto import get_random_string
from unittest import TestCase

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from garpix_notify.models import Notify
from garpix_notify.models import NotifyCategory
from garpix_notify.models import NotifyTemplate
from garpix_notify.models import NotifyUserList
from garpix_notify.models import NotifyUserListParticipant
from garpix_notify.models.choices import TYPE

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings")
django.setup()


class PreBuildTestCase(TestCase):
    def setUp(self):
        # нулевой евент, только для теста
        self.PASS_TEST_EVENT = 0
        self.PASS_TEST_EVENT_1 = 1
        self.PASS_TEST_EVENT_2 = 2
        # тестовый пользователь
        self.data_user = {
            'username': 'email_test' + get_random_string(length=4),
            'email': 'test@garpix.com',
            'password': 'BlaBla123',
            'first_name': 'Ivan',
            'last_name': 'Ivanov',
        }
        # data
        self.data_template_email = {
            'title': 'Тестовый темплейт',
            'subject': 'Тестовый темплейт {{user.email}}',
            'text': 'Контент текстовый {{user.email}} - {{sometext}}',
            'html': 'Контент HTML {{user.email}} - {{sometext}}',
            'type': TYPE.EMAIL,
            'event': self.PASS_TEST_EVENT,
        }
        self.data_category = {
            'title': 'Основная категория_' + get_random_string(length=4),
            'template': '<div>{{text}}</div>',
        }
        self.sometext = 'bla bla'
        self.data_compiled_email = {
            'subject': f'Тестовый темплейт {self.data_user["email"]}',
            'text': f'Контент текстовый {self.data_user["email"]} - {self.sometext}',
            'html': f'Контент HTML {self.data_user["email"]} - {self.sometext}',
            'type': TYPE.EMAIL,
            'event': self.PASS_TEST_EVENT,
        }
        super().setUp()

    def test_notify_email_positive(self):
        # Создание пользователя
        User = get_user_model()
        user = User.objects.create_user(**self.data_user)
        # Создание категории
        category = NotifyCategory.objects.create(**self.data_category)
        category = NotifyCategory.objects.get(pk=category.pk)
        self.assertEqual(category.title, self.data_category['title'])
        self.assertEqual(category.template, self.data_category['template'])
        # Создание шаблона
        template_email = NotifyTemplate.objects.create(category=category, **self.data_template_email)
        template_email = NotifyTemplate.objects.get(pk=template_email.pk)
        self.assertEqual(template_email.title, self.data_template_email['title'])
        self.assertEqual(template_email.subject, self.data_template_email['subject'])
        self.assertEqual(template_email.text, self.data_template_email['text'])
        self.assertEqual(template_email.html, self.data_template_email['html'])
        self.assertEqual(template_email.type, self.data_template_email['type'])
        self.assertEqual(template_email.event, self.data_template_email['event'])
        self.assertEqual(template_email.category.id, category.id)
        # Создание пробного письма
        notify = Notify.send(self.PASS_TEST_EVENT, {
            'sometext': self.sometext,
            'user': user,
        }, user=user)
        self.assertEqual(notify[0].event, template_email.event)
        self.assertEqual(notify[0].subject, self.data_compiled_email['subject'])
        self.assertEqual(notify[0].text, self.data_compiled_email['text'])
        self.assertEqual(notify[0].html, self.data_compiled_email['html'])
        self.assertEqual(notify[0].type, self.data_compiled_email['type'])
        self.assertEqual(notify[0].event, self.data_compiled_email['event'])

    def test_notify_email_user_list(self):
        self.data_template_email_1 = {
            'title': 'Тестовый темплейт',
            'subject': 'Тестовый темплейт {{user.email}}',
            'text': 'Контент текстовый {{user.email}} - {{sometext}}',
            'html': 'Контент HTML {{user.email}} - {{sometext}}',
            'type': TYPE.EMAIL,
            'event': self.PASS_TEST_EVENT_1,
        }
        self.data_compiled_email_1 = {
            'subject': f'Тестовый темплейт {self.data_user["email"]}',
            'text': f'Контент текстовый {self.data_user["email"]} - {self.sometext}',
            'html': f'Контент HTML {self.data_user["email"]} - {self.sometext}',
            'type': TYPE.EMAIL,
            'event': self.PASS_TEST_EVENT_1
        }
        # Создание пользователя
        User = get_user_model()
        user = User.objects.create_user(**self.data_user)
        # Создание списка
        user_list = NotifyUserList.objects.create(title='userlist_' + get_random_string(length=4))
        group = Group.objects.create(name='group_' + get_random_string(length=4))
        user_list.user_groups.add(group)

        user_list_participant1 = NotifyUserListParticipant.objects.create(  # noqa
            user_list=user_list,
            email='test2@garpix.com',
        )
        user_list_participant2 = NotifyUserListParticipant.objects.create(  # noqa
            user_list=user_list,
        )
        user_list_participant3 = NotifyUserListParticipant.objects.create(  # noqa
            user_list=user_list,
            email='test3@garpix.com',
        )

        # Создание категории
        category = NotifyCategory.objects.create(**self.data_category)
        category = NotifyCategory.objects.get(pk=category.pk)
        self.assertEqual(category.title, self.data_category['title'])
        self.assertEqual(category.template, self.data_category['template'])

        # Создание шаблона
        template_email = NotifyTemplate.objects.create(category=category, **self.data_template_email_1)
        template_email = NotifyTemplate.objects.get(pk=template_email.pk)
        template_email.user_lists.add(user_list)
        template_email.save()

        self.assertEqual(template_email.title, self.data_template_email_1['title'])
        self.assertEqual(template_email.subject, self.data_template_email_1['subject'])
        self.assertEqual(template_email.text, self.data_template_email_1['text'])
        self.assertEqual(template_email.html, self.data_template_email_1['html'])
        self.assertEqual(template_email.type, self.data_template_email_1['type'])
        self.assertEqual(template_email.event, self.data_template_email_1['event'])
        self.assertEqual(template_email.category.id, category.id)

        # Создание пробного письма
        notify = Notify.send(self.PASS_TEST_EVENT_1, {
            'sometext': self.sometext,
            'user': user,
        }, user=user)

        self.assertEqual(notify[0].event, template_email.event)

        # notify
        self.assertEqual(notify[0].subject, self.data_compiled_email_1['subject'])
        self.assertEqual(notify[0].text, self.data_compiled_email_1['text'])
        self.assertEqual(notify[0].html, self.data_compiled_email_1['html'])
        self.assertEqual(notify[0].type, self.data_compiled_email_1['type'])
        self.assertEqual(notify[0].event, self.data_compiled_email_1['event'])
        self.assertEqual(notify[0].email, 'test@garpix.com')

    def test_notify_viber(self):
        self.data_template_viber = {
            'title': 'Тестовый темплейт',
            'subject': 'Тестовый темплейт {{user.viber_chat_id}}',
            'text': 'Контент текстовый {{user.viber_chat_id}} - {{sometext}}',
            'html': 'Контент HTML {{user.viber_chat_id}} - {{sometext}}',
            'type': TYPE.VIBER,
            'event': self.PASS_TEST_EVENT_2,
        }
        self.data_viber_user = {
            'username': 'viber_' + get_random_string(length=5),
            'viber_secret_key': '111',
            'viber_chat_id': 'm4FsaRu5kBi8HzSAC0liFQ==',
            'password': 'BlaBla123',
            'first_name': 'IvanViber',
            'last_name': 'IvanovViber',
        }
        self.data_compiled_viber = {
            'subject': f'Тестовый темплейт {self.data_viber_user["viber_chat_id"]}',
            'text': f'Контент текстовый {self.data_viber_user["viber_chat_id"]} - {self.sometext}',
            'html': f'Контент HTML {self.data_viber_user["viber_chat_id"]} - {self.sometext}',
            'type': TYPE.VIBER,
            'event': self.PASS_TEST_EVENT_2,
        }
        # Создание пользователя
        User = get_user_model()
        user = User.objects.create_user(**self.data_viber_user)
        # Создание списка
        user_list = NotifyUserList.objects.create(title='viber_' + get_random_string(length=4))
        user_list_participant1 = NotifyUserListParticipant.objects.create(  # noqa
            user_list=user_list,
        )
        # Создание категории
        category = NotifyCategory.objects.create(**self.data_category)
        category = NotifyCategory.objects.get(pk=category.pk)

        self.assertEqual(category.title, self.data_category['title'])
        self.assertEqual(category.template, self.data_category['template'])

        # Создание шаблона
        template_viber = NotifyTemplate.objects.create(**self.data_template_viber, category=category)
        template_viber = NotifyTemplate.objects.get(pk=template_viber.pk)
        template_viber.user_lists.add(user_list)
        template_viber.save()

        self.assertEqual(template_viber.title, self.data_template_viber['title'])
        self.assertEqual(template_viber.subject, self.data_template_viber['subject'])
        self.assertEqual(template_viber.text, self.data_template_viber['text'])
        self.assertEqual(template_viber.html, self.data_template_viber['html'])
        self.assertEqual(template_viber.type, self.data_template_viber['type'])
        self.assertEqual(template_viber.event, self.data_template_viber['event'])
        self.assertEqual(template_viber.category.id, category.id)

        # Создание уведомления
        notify = Notify.send(self.PASS_TEST_EVENT_2, {
            'sometext': self.sometext,
            'user': user,
        }, user=user)

        self.assertEqual(notify[0].event, template_viber.event)

        # notify
        self.assertEqual(notify[0].subject, self.data_compiled_viber['subject'])
        self.assertEqual(notify[0].text, self.data_compiled_viber['text'])
        self.assertEqual(notify[0].html, self.data_compiled_viber['html'])
        self.assertEqual(notify[0].type, self.data_compiled_viber['type'])
        self.assertEqual(notify[0].event, self.data_compiled_viber['event'])
        self.assertEqual(notify[0].user.viber_chat_id, 'm4FsaRu5kBi8HzSAC0liFQ==')
