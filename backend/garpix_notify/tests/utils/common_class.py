from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.utils.crypto import get_random_string

from garpix_notify.models import NotifyCategory, NotifyTemplate, NotifyUserList, NotifyUserListParticipant


class CommonTestClass:

    def create_user(self, user_data: dict):
        user = get_user_model().objects.create_user(**user_data)
        return user

    def create_category(self, category_data: dict):
        category = NotifyCategory.objects.create(**category_data)
        return category

    def create_template(self, template_data: dict, category: NotifyCategory, user_list: NotifyUserList = None):
        template = NotifyTemplate.objects.create(category=category, **template_data)

        if user_list:
            template.user_lists.add(user_list)
            template.save()

        return template

    def create_user_list(self):
        user_list = NotifyUserList.objects.create(title='userlist_' + get_random_string(length=4))
        group = Group.objects.create(name='group_' + get_random_string(length=4))
        user_list.user_groups.add(group)

        user_list_participant_data: list = [{
            'user_list': user_list,
            'email': f'{get_random_string(length=5)}@garpix.com'
        } for _ in range(5)]

        for participant in user_list_participant_data:
            NotifyUserListParticipant.objects.create(**participant)

        return user_list
