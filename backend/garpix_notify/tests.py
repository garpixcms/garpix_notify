from django.test import TestCase
from .models import NotifyTemplate
from .models import NotifyCategory
from .models import Notify
from .models import NotifyUserList
from .models import NotifyUserListParticipant
from .models.choices import TYPE
from django.contrib.auth import get_user_model

User = get_user_model()


class PreBuildTestCase(TestCase):
    def setUp(self):
        # нулевой евент, только для теста
        self.PASS_TEST_EVENT = 0
        # тестовый пользователь
        self.data_user = {
            'username': 'test',
            'email': 'test@garpix.com',
            'password': 'BlaBla123',
            'first_name': 'Ivan',
            'last_name': 'Ivanov',
        }
        # data
        self.data_category = {
            'title': 'Основная категория',
            'template': '<div>{{text}}</div>',
        }
        self.data_template_email = {
            'title': 'Тестовый темплейт',
            'subject': 'Тестовый темплейт {{user.email}}',
            'text': 'Контент текстовый {{user.email}} - {{sometext}}',
            'html': 'Контент HTML {{user.email}} - {{sometext}}',
            'type': TYPE.EMAIL,
            'event': self.PASS_TEST_EVENT,
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
        Notify.send(self.PASS_TEST_EVENT, {
            'sometext': self.sometext,
            'user': user,
        }, user=user)
        self.assertEqual(Notify.objects.all().count(), 1)
        notify = Notify.objects.all().first()
        self.assertEqual(notify.subject, self.data_compiled_email['subject'])
        self.assertEqual(notify.text, self.data_compiled_email['text'])
        self.assertEqual(notify.html, self.data_compiled_email['html'])
        self.assertEqual(notify.type, self.data_compiled_email['type'])
        self.assertEqual(notify.event, self.data_compiled_email['event'])

    def test_notify_email_user_list(self):
        # Создание пользователя
        user = User.objects.create_user(**self.data_user)
        # Создание категории
        category = NotifyCategory.objects.create(**self.data_category)
        category = NotifyCategory.objects.get(pk=category.pk)
        self.assertEqual(category.title, self.data_category['title'])
        self.assertEqual(category.template, self.data_category['template'])
        # Создание списка
        user_list = NotifyUserList.objects.create(title='Админы')
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
        # Создание шаблона
        template_email = NotifyTemplate.objects.create(category=category, **self.data_template_email)
        template_email.user_lists.add(user_list)
        template_email = NotifyTemplate.objects.get(pk=template_email.pk)
        self.assertEqual(template_email.title, self.data_template_email['title'])
        self.assertEqual(template_email.subject, self.data_template_email['subject'])
        self.assertEqual(template_email.text, self.data_template_email['text'])
        self.assertEqual(template_email.html, self.data_template_email['html'])
        self.assertEqual(template_email.type, self.data_template_email['type'])
        self.assertEqual(template_email.event, self.data_template_email['event'])
        self.assertEqual(template_email.category.id, category.id)
        # Создание пробного письма
        Notify.send(self.PASS_TEST_EVENT, {
            'sometext': self.sometext,
            'user': user,
        }, user=user)
        self.assertEqual(Notify.objects.all().count(), 3)  # пустой не должен был отправиться "user_list_participant2"
        # notify 1
        notify = Notify.objects.get(user=user)
        self.assertEqual(notify.subject, self.data_compiled_email['subject'])
        self.assertEqual(notify.text, self.data_compiled_email['text'])
        self.assertEqual(notify.html, self.data_compiled_email['html'])
        self.assertEqual(notify.type, self.data_compiled_email['type'])
        self.assertEqual(notify.event, self.data_compiled_email['event'])
        self.assertEqual(notify.email, 'test@garpix.com')
        # notify 2
        notify = Notify.objects.get(email='test2@garpix.com')
        self.assertEqual(notify.subject, self.data_compiled_email['subject'])
        self.assertEqual(notify.text, self.data_compiled_email['text'])
        self.assertEqual(notify.html, self.data_compiled_email['html'])
        self.assertEqual(notify.type, self.data_compiled_email['type'])
        self.assertEqual(notify.event, self.data_compiled_email['event'])
        self.assertEqual(notify.email, 'test2@garpix.com')
        # notify 3
        notify = Notify.objects.get(email='test3@garpix.com')
        self.assertEqual(notify.subject, self.data_compiled_email['subject'])
        self.assertEqual(notify.text, self.data_compiled_email['text'])
        self.assertEqual(notify.html, self.data_compiled_email['html'])
        self.assertEqual(notify.type, self.data_compiled_email['type'])
        self.assertEqual(notify.event, self.data_compiled_email['event'])
        self.assertEqual(notify.email, 'test3@garpix.com')

    def test_notify_viber(self):
        self.data_template_viber = {
            'title': 'Тестовый темплейт',
            'subject': 'Тестовый темплейт {{user.viber_chat_id}}',
            'text': 'Контент текстовый {{user.viber_chat_id}} - {{sometext}}',
            'html': 'Контент HTML {{user.viber_chat_id}} - {{sometext}}',
            'type': TYPE.VIBER,
            'event': self.PASS_TEST_EVENT,
        }
        self.data_viber_user = {
            'username': 'test',
            'viber_secret_key': '111',
            'viber_chat_id': 'm4FsaRu5kBi8HzSAC0liFQ==',
            'password': 'BlaBla123',
            'first_name': 'Ivan',
            'last_name': 'Ivanov',
        }
        self.data_compiled_viber = {
            'subject': f'Тестовый темплейт {self.data_viber_user["viber_chat_id"]}',
            'text': f'Контент текстовый {self.data_viber_user["viber_chat_id"]} - {self.sometext}',
            'html': f'Контент HTML {self.data_viber_user["viber_chat_id"]} - {self.sometext}',
            'type': TYPE.VIBER,
            'event': self.PASS_TEST_EVENT,
        }
        # Создание пользователя
        user = User.objects.create_user(**self.data_viber_user)
        # Создание категории
        category = NotifyCategory.objects.create(**self.data_category)
        category = NotifyCategory.objects.get(pk=category.pk)
        self.assertEqual(category.title, self.data_category['title'])
        self.assertEqual(category.template, self.data_category['template'])
        # Создание списка
        user_list = NotifyUserList.objects.create(title='viber_user_list')
        user_list_participant1 = NotifyUserListParticipant.objects.create(  # noqa
            user_list=user_list,
        )
        template_viber = NotifyTemplate.objects.create(category=category, **self.data_template_viber)
        template_viber.user_lists.add(user_list)
        template_viber = NotifyTemplate.objects.get(pk=template_viber.pk)
        self.assertEqual(template_viber.title, self.data_template_viber['title'])
        self.assertEqual(template_viber.subject, self.data_template_viber['subject'])
        self.assertEqual(template_viber.text, self.data_template_viber['text'])
        self.assertEqual(template_viber.html, self.data_template_viber['html'])
        self.assertEqual(template_viber.type, self.data_template_viber['type'])
        self.assertEqual(template_viber.event, self.data_template_viber['event'])
        self.assertEqual(template_viber.category.id, category.id)

        Notify.send(self.PASS_TEST_EVENT, {
            'sometext': self.sometext,
            'user': user,
        }, user=user)
        self.assertEqual(Notify.objects.all().count(), 1)

        # notify 1
        notify = Notify.objects.get(user=user)
        self.assertEqual(notify.subject, self.data_compiled_viber['subject'])
        self.assertEqual(notify.text, self.data_compiled_viber['text'])
        self.assertEqual(notify.html, self.data_compiled_viber['html'])
        self.assertEqual(notify.type, self.data_compiled_viber['type'])
        self.assertEqual(notify.event, self.data_compiled_viber['event'])
        self.assertEqual(notify.user.viber_chat_id, 'm4FsaRu5kBi8HzSAC0liFQ==')
