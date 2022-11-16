from typing import Optional

from django.contrib.auth import get_user_model


class ReceivingUsers:

    def __init__(self, users_list: list, value: Optional[str] = None):
        self.receivers = []
        self.users_list = users_list
        self.value = value

    def __returning_specific_list(self, receivers: list) -> list:
        receivers_list = list(set(map(lambda x: x.get(self.value), receivers)))
        return receivers_list

    def __forming_data_list(self, queryset) -> list:
        data_list = [{'user': user,
                      'email': user.email,
                      'phone': user.phone,
                      'viber_chat_id': user.viber_chat_id,
                      'telegram_chat_id': user.telegram_chat_id} for user in queryset]
        return data_list

    def __receiving_users(self) -> list:  # noqa: C901
        user_model = get_user_model()

        for user_list in self.users_list:
            # Массовая рассылка по всем пользователям сайта
            if user_list.mail_to_all:
                users = user_model.objects.all()
                data_list: list = self.__forming_data_list(users)
                self.receivers.extend(data_list)

                if self.value:
                    return self.__returning_specific_list(self.receivers)
                return self.receivers

            # Выполняем запросы
            users_participants = user_list.participants.all()
            user_groups_qs = user_list.user_groups.all()
            users_qs = user_list.users.all()

            # Собираем данные из дополнительного списка получателей, если он есть.
            if users_participants.exists():
                self.receivers.extend([{
                    'user': participant.user,
                    'email': participant.user.email if participant.user else participant.email,
                    'phone': participant.user.phone if participant.user else participant.phone,
                    'viber_chat_id': (
                        participant.user.viber_chat_id if participant.user else participant.viber_chat_id
                    ),
                    'telegram_chat_id': (
                        participant.user.telegram_chat_id if participant.user else participant.telegram_chat_id
                    ),
                } for participant in users_participants])

            # Собираем данные из групп, которые входят в список рассылки
            if user_groups_qs.exists():
                group_users = user_model.objects.prefetch_related('groups').filter(groups__in=user_groups_qs)
                if group_users.exists():
                    data_list: list = self.__forming_data_list(group_users)
                    self.receivers.extend(data_list)

            # Собираем данные по пользователям, если они были переданы
            if users_qs.exists():
                data_list: list = self.__forming_data_list(users_qs)
                self.receivers.extend(data_list)

        if self.value:
            return self.__returning_specific_list(self.receivers)

        return self.receivers

    @classmethod
    def run_receiving_users(cls, users_list: list, value: str = None) -> list:
        return cls(users_list, value).__receiving_users()
