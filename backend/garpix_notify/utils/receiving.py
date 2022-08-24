from django.contrib.auth import get_user_model


class ReceivingUsers:

    def __init__(self, users_list: list, value: str = None):
        self.users_list = users_list
        self.value = value

    def __returning_specific_list(self, receivers: list) -> list:
        # Убираем дубликаты пользователей для переданного значения из функции
        receivers_dict = list({v[self.value]: v for v in receivers}.values())
        receivers_new = [user.get(self.value) for user in receivers_dict]
        return receivers_new

    def __receiving_users(self) -> list:  # noqa: C901
        user_model = get_user_model()
        receivers: list = []
        for user_list in self.users_list:
            # Проверяем рассылку, не отмечена ли массовая рассылка
            if user_list.mail_to_all:
                users = user_model.objects.all()
                receivers.extend([
                    {'user': user,
                     'email': user.email,
                     'phone': user.phone,
                     'viber_chat_id': user.viber_chat_id
                     } for user in users
                ])

                if self.value:
                    return self.__returning_specific_list(receivers)
                return receivers

            # Собираем данные из дополнительного списка получателей, если он есть.
            users_participants = user_list.participants.all()
            if users_participants.exists():
                for participant in users_participants:
                    if participant.user or participant.email or participant.phone or participant.viber_chat_id:
                        receivers.append({
                            'user': participant.user,
                            'email': participant.user.email if participant.user else participant.email,
                            'phone': participant.user.phone if participant.user else participant.phone,
                            'viber_chat_id':
                                participant.user.viber_chat_id if participant.user else participant.viber_chat_id
                        })

            # Собираем данные из групп, которые входят в список рассылки
            user_groups_qs = user_list.user_groups.all()
            if user_groups_qs.exists():
                group_users = user_model.objects.prefetch_related('groups').filter(groups__in=user_groups_qs)

                if group_users.exists():
                    receivers.extend([
                        {'user': user,
                         'email': user.email,
                         'phone': user.phone,
                         'viber_chat_id': user.viber_chat_id
                         } for user in group_users
                    ])

            # Собираем данные по пользователям, если они были переданы
            users_qs = user_list.users.all()
            if users_qs.exists():
                receivers.extend([
                    {
                        'user': user,
                        'email': user.email,
                        'phone': user.phone,
                        'viber_chat_id': user.viber_chat_id
                    } for user in users_qs
                ])

        if self.value:
            return self.__returning_specific_list(receivers)

        return receivers

    @classmethod
    def run_receiving_users(cls, users_list: list, value: str = None) -> list:
        return cls(users_list, value).__receiving_users()
