import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from ..models import NotifyUserList, NotifyUserListParticipant
from ..utils.receiving import ReceivingUsers
from .utils.common_class import CommonTestClass
from .utils.generate_data import generate_users


User = get_user_model()


@pytest.mark.django_db
class TestReceivingUsers(CommonTestClass):
    @pytest.fixture
    def users(self):
        users = generate_users(8)
        return User.objects.bulk_create([
            User(**data)
            for data in users
        ])

    @pytest.fixture
    def users_list_all(self):
        users_list = NotifyUserList.objects.bulk_create([
            NotifyUserList(
                title='Receivers all users',
                mail_to_all=True,
            ),

        ])
        return users_list

    @pytest.fixture
    def users_list_complex(self, users):
        users_list = NotifyUserList.objects.create(
            title='Receivers complex',
        )

        # Participants (0 and 1 user)
        NotifyUserListParticipant.objects.bulk_create([
            NotifyUserListParticipant(user=users[0], user_list=users_list),
            NotifyUserListParticipant(email=users[1].email, user_list=users_list),
        ])

        # Groups (2 and 3 user)
        group = Group.objects.create(name='Test group')
        group.user_set.add(*users[2:4])
        users_list.user_groups.add(group)

        # Simple users (4 and 5 user)
        users_list.users.add(*users[4:6])

        return [users_list]

    def test_receivers_all(self, users, users_list_all):
        result = ReceivingUsers.run_receiving_users(users_list_all)
        assert len(result) == 8
        assert {
            'user': users[0],
            'email': users[0].email,
            'phone': users[0].phone,
            'viber_chat_id': '',
            'telegram_chat_id': '',
        } in result

    def test_receivers_all_with_value(self, users, users_list_all):
        result = ReceivingUsers.run_receiving_users(users_list_all, 'email')
        assert len(result) == 8
        assert users[0].email in result

    def test_receivers_complex(self, users, users_list_complex):
        result = ReceivingUsers.run_receiving_users(users_list_complex)
        assert len(result) == 6

        # Participants (0 and 1)
        assert {
            'user': users[0],
            'email': users[0].email,
            'phone': users[0].phone,
            'viber_chat_id': '',
            'telegram_chat_id': '',
        } == result[0]
        assert {
            'user': None,
            'email': users[1].email,
            'phone': '',
            'viber_chat_id': '',
            'telegram_chat_id': '',
        } == result[1]

        # Groups (2 and 3)
        assert {
            'user': users[2],
            'email': users[2].email,
            'phone': users[2].phone,
            'viber_chat_id': '',
            'telegram_chat_id': '',
        } == result[2]
        assert {
            'user': users[3],
            'email': users[3].email,
            'phone': users[3].phone,
            'viber_chat_id': '',
            'telegram_chat_id': '',
        } == result[3]

        # Simple users (4 and 5)
        assert {
            'user': users[4],
            'email': users[4].email,
            'phone': users[4].phone,
            'viber_chat_id': '',
            'telegram_chat_id': '',
        } == result[4]
        assert {
            'user': users[5],
            'email': users[5].email,
            'phone': users[5].phone,
            'viber_chat_id': '',
            'telegram_chat_id': '',
        } == result[5]

    def test_receivers_complex_with_value(self, users, users_list_complex):
        result = ReceivingUsers.run_receiving_users(users_list_complex, 'email')
        assert len(result) == 6

        # Participants (0 and 1)
        assert users[0].email in result
        assert users[1].email in result

        # Groups (2 and 3)
        assert users[2].email in result
        assert users[3].email in result

        # Simple users (4 and 5)
        assert users[4].email in result
        assert users[5].email in result

    def test_receivers_with_invalid_key(self, users_list_all):
        result = ReceivingUsers.run_receiving_users(users_list_all, 'invalid_key')
        assert len(result) == 0
