from django.contrib.auth import get_user_model


class ReceivingUsers:

    def __init__(self, users_list: list, value: str = None):
        self.users_list = users_list
        self.value = value

    def __returning_specific_list(self, receivers: list) -> list:
        receivers_dict = list({v[self.value]: v for v in receivers}.values())
        receivers_new = [user.get(self.value) for user in receivers_dict]
        return receivers_new

    def __forming_data_list(self, queryset) -> list:
        data_list = [{'user': user,
                      'email': user.email,
                      'phone': user.phone,
                      'viber_chat_id': user.viber_chat_id,
                      'telegram_chat_id': user.telegram_chat_id
                      } for user in queryset]
        return data_list

    def __receiving_users(self) -> list:  # noqa: C901
        user_model = get_user_model()
        receivers: list = []
        for user_list in self.users_list:
            # Массовая рассылка по всем пользователям сайта
            if user_list.mail_to_all:
                users = user_model.objects.all()
                data_list: list = self.__forming_data_list(users)
                receivers.extend(data_list)

                if self.value:
                    return self.__returning_specific_list(receivers)
                return receivers

            # Выполняем запросы
            users_participants = user_list.participants.all()
            user_groups_qs = user_list.user_groups.all()
            users_qs = user_list.users.all()

            # Собираем данные из дополнительного списка получателей, если он есть.
            if users_participants.exists():
                receivers.extend([{
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
                    receivers.extend(data_list)

            # Собираем данные по пользователям, если они были переданы
            if users_qs.exists():
                data_list: list = self.__forming_data_list(users_qs)
                receivers.extend(data_list)

        if self.value:
            return self.__returning_specific_list(receivers)

        return receivers

    @classmethod
    def run_receiving_users(cls, users_list: list, value: str = None) -> list:
        return cls(users_list, value).__receiving_users()
