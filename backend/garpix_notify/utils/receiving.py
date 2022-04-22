from django.contrib.auth import get_user_model
from django.db.models import Q


def receiving(users_list):
    User = get_user_model()
    for user_list in users_list:
        recievers = []
        # Сначала проверям есть ли допольнительные список получателей
        # Если у участника из дополнительного списка ничего не заполнено - не отправляем уведомление
        for participant in user_list.participants.all():
            if participant.user or participant.email:
                recievers.append({
                    'user': participant.user,
                    'email': participant.email,
                    'phone': participant.phone,
                    'viber_chat_id': participant.viber_chat_id,
                })
        # Проверяем в не отмечена ли массовая рассылка
        if user_list.mail_to_all is False:
            group_users = User.objects.filter(
                Q(groups__in=list(
                    user_list.user_groups.all()
                )))
            for user in group_users:
                recievers.append(
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
                recievers.append(
                    {
                        'user': user,
                        'email': user.email,
                        'phone': user.phone,
                        'viber_chat_id': user.viber_chat_id,
                    }
                )
        return recievers
