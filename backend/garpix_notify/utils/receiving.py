from django.contrib.auth import get_user_model
from django.db.models import Q


def receiving_users(users_list, value=False):
    User = get_user_model()
    for user_list in users_list:
        receivers = []
        # Сначала проверям есть ли дополнительные списки получателей
        for participant in user_list.participants.all():
            if participant.user or participant.email:
                receivers.append({
                    'user': participant.user,
                    'email': participant.user.email if participant.user else participant.email,
                    'phone': participant.user.phone if participant.user else participant.email,
                    'viber_chat_id': participant.user.viber_chat_id if participant.user else participant.viber_chat_id
                })
        # Проверяем рассылку, не отмечена ли массовая рассылка
        if user_list.mail_to_all is False:
            group_users = User.objects.filter(
                Q(groups__in=list(
                    user_list.user_groups.all()
                )))
            for user in group_users:
                receivers.append(
                    {
                        'user': user,
                        'email': user.email,
                        'phone': user.phone,
                        'viber_chat_id': user.viber_chat_id,
                    }
                )
        else:
            users = User.objects.all()
            for user in users:
                receivers.append(
                    {
                        'user': user,
                        'email': user.email,
                        'phone': user.phone,
                        'viber_chat_id': user.viber_chat_id,
                    }
                )
        # Убираем дубликаты пользователей для переданного значения из функции
        if value:
            receivers = list({v[value]: v for v in receivers}.values())
            receivers_new = []
            for user in receivers:
                if user[value]:
                    receivers_new.append(user[value])
            return receivers_new

        return receivers
