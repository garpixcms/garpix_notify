import django
import os

from django.utils.crypto import get_random_string
from unittest import TestCase

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from garpix_notify.models import SystemNotify
from garpix_notify.models import NotifyCategory
from garpix_notify.models import NotifyTemplate
from garpix_notify.models import NotifyUserList
from garpix_notify.models import NotifyUserListParticipant
from garpix_notify.models.choices import TYPE


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings")
django.setup()


class SystemNotifyTestCase(TestCase):

    def setUp(self):
        # test events
        self.PASS_TEST_EVENT = 0
        self.PASS_TEST_EVENT_1 = 1

        # data for test user
        self.data_user = {
            'username': 'email_test' + get_random_string(length=4),
            'email': 'test@garpix.com',
            'password': 'BlaBla123',
            'first_name': 'Ivan',
            'last_name': 'Ivanov',
        }

        # some data
        self.some_key = f"{get_random_string(length=4)}"
        self.some_text = f"{get_random_string(length=7)}"
        self.some_data_dict = {self.some_key: self.some_text}
        self.data_template_email = {
            'title': 'Тестовый системный темплейт',
            'subject': 'Тестовый темплейт',
            'text': self.some_data_dict,
            'html': self.some_data_dict,
            'type': TYPE.SYSTEM,
            'event': self.PASS_TEST_EVENT,
        }
        self.data_category = {
            'title': 'Тестовая категория_' + get_random_string(length=4),
            'template': '<div>{{text}}</div>',
        }
        super().setUp()

    def test_system_notify_positive(self):
        # Create user
        User = get_user_model()
        user = User.objects.create_user(**self.data_user)

        # Create category
        category = NotifyCategory.objects.create(**self.data_category)
        category = NotifyCategory.objects.filter(pk=category.pk).first()
        self.assertEqual(category.title, self.data_category['title'])
        self.assertEqual(category.template, self.data_category['template'])

        # Create template
        template_email = NotifyTemplate.objects.create(category=category, **self.data_template_email)
        self.assertEqual(template_email.title, self.data_template_email['title'])
        self.assertEqual(template_email.subject, self.data_template_email['subject'])
        self.assertEqual(template_email.text, self.data_template_email['text'])
        self.assertEqual(template_email.html, self.data_template_email['html'])
        self.assertEqual(template_email.type, self.data_template_email['type'])
        self.assertEqual(template_email.event, self.data_template_email['event'])
        self.assertEqual(template_email.category.id, category.id)

        # Create system notify
        SystemNotify.send(
            self.some_data_dict, user=user, event=self.PASS_TEST_EVENT
        )
        notify = SystemNotify.objects.filter(user=user, event=self.PASS_TEST_EVENT).first()
        data_compiled_email = {
            "title": f'{user} - room_{user.pk}',
            "text": f"{self.some_data_dict}, "
                    f'"event_id": {self.data_template_email["event"]}, '
                    f"user: {user.pk}",
            "type": TYPE.SYSTEM,
            "event": self.PASS_TEST_EVENT,
        }
        self.assertEqual(notify.event, template_email.event)
        self.assertEqual(notify.title, data_compiled_email["title"])
        # self.assertEqual(notify.data_json, data_compiled_email["text"])
        self.assertEqual(notify.type, data_compiled_email["type"])
        self.assertEqual(notify.event, data_compiled_email["event"])

    def test_system_notify_user_list(self):
        # test template data
        self.data_template_system_1 = {
            'title': 'Тестовый системный темплейт массовая рассылка',
            'subject': 'Тестовый темплейт',
            'text': f'{self.some_data_dict}',
            'html': f'{self.some_data_dict}',
            'type': TYPE.SYSTEM,
            'event': self.PASS_TEST_EVENT_1,
        }

        # Create user lists
        user_list = NotifyUserList.objects.create(title='userlist_' + get_random_string(length=4))
        group = Group.objects.create(name='group_' + get_random_string(length=4))
        user_list.user_groups.add(group)

        # Participant data
        self.user_list_participant_data = [
            {'user_list': user_list, 'email': 'test2@garpix.com'},
            {'user_list': user_list}
        ]
        for user_list_data in self.user_list_participant_data:
            NotifyUserListParticipant.objects.create(**user_list_data)

        # Create users
        user_model = get_user_model()
        user_data_list = [
            {
                'username': f'user_{user_count}_' + get_random_string(length=3),
                'email': f'{get_random_string(length=5).capitalize()}@garpix.com',
                'password': f'1{get_random_string(length=9)}1',
                'first_name': get_random_string(length=5),
                'last_name': get_random_string(length=5),
            } for user_count in range(10)
        ]
        for user_data in user_data_list:
            user = user_model.objects.create_user(**user_data)
            user.groups.add(group)
            user.save()

        # Create category
        category = NotifyCategory.objects.create(**self.data_category)
        self.assertEqual(category.title, self.data_category['title'])
        self.assertEqual(category.template, self.data_category['template'])

        # Create template
        template_notify = NotifyTemplate.objects.create(category=category, **self.data_template_system_1)
        template_notify = NotifyTemplate.objects.get(pk=template_notify.pk)
        template_notify.user_lists.add(user_list)
        template_notify.save()

        self.assertEqual(template_notify.title, self.data_template_system_1['title'])
        self.assertEqual(template_notify.subject, self.data_template_system_1['subject'])
        self.assertEqual(template_notify.text, self.data_template_system_1['text'])
        self.assertEqual(template_notify.html, self.data_template_system_1['html'])
        self.assertEqual(template_notify.type, self.data_template_system_1['type'])
        self.assertEqual(template_notify.event, self.data_template_system_1['event'])
        self.assertEqual(template_notify.category.id, category.id)

        # Create system notify
        SystemNotify.send(self.some_data_dict, event=self.PASS_TEST_EVENT_1)
        notify_qs = SystemNotify.objects.select_related('user').filter(
            event=self.PASS_TEST_EVENT_1
        ).order_by('user__id')

        # Test system notify
        for notify in notify_qs:
            user = user_model.objects.filter(pk=notify.user.pk).first()
            self.data_compiled_system_1 = {
                'title': f'{user.username} - room_{user.pk}',
                'text': f'{self.some_data_dict}, '
                        f'event_id: {self.data_template_email["event"]}, '
                        f'user: {user.pk}',
                'type': TYPE.SYSTEM,
                'event': self.PASS_TEST_EVENT_1,
            }

            # self.assertEqual(notify.title, self.data_compiled_system_1['title'])
            # self.assertEqual(notify.data_json, self.data_compiled_system_1['text'])
            self.assertEqual(notify.type, self.data_compiled_system_1['type'])
            self.assertEqual(notify.event, self.data_compiled_system_1['event'])
