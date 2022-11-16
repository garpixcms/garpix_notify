from django.utils.crypto import get_random_string
from garpix_notify.models.choices import TYPE

some_text = 'bla bla'


def generate_users(count: int) -> list:
    users_list = [{
        'username': f'user_{i}',
        'email': f'{get_random_string(length=4)}@garpix.com',
        'password': f'BlaBla123{get_random_string(length=4)}',
        'first_name': f'{get_random_string(length=5)}',
        'last_name': f'{get_random_string(length=8)}',
    } for i in range(count)]
    return users_list


def generate_viber_user(count: int) -> list:
    users_list = [{
        'username': 'viber_' + get_random_string(length=5),
        'email': f'{get_random_string(length=4)}@garpix.com',
        'viber_secret_key': get_random_string(length=5, allowed_chars='1234567890'),
        'viber_chat_id': 'm4FsaRu5kBi8HzSAC0liFQ==',
        'password': f'BlaBla123{get_random_string(length=4)}',
        'first_name': f'{get_random_string(length=5)}',
        'last_name': f'{get_random_string(length=8)}',
    } for i in range(count)]
    return users_list


def generate_templates(event: int) -> list:
    return [{
        'title': 'Тестовый темплейт',
        'subject': 'Тестовый темплейт {{user.email}}',
        'text': 'Контент текстовый {{user.email}} - {{sometext}}',
        'html': 'Контент HTML {{user.email}} - {{sometext}}',
        'type': TYPE.EMAIL,
        'event': event,
    }]


def generate_templates_viber(event: int) -> list:
    return [{
        'title': 'Тестовый темплейт вайбер',
        'subject': 'Тестовый темплейт {{user.viber_chat_id}}',
        'text': 'Контент текстовый {{user.viber_chat_id}} - {{sometext}}',
        'html': 'Контент HTML {{user.viber_chat_id}} - {{sometext}}',
        'type': TYPE.VIBER,
        'event': event,
    }]


def generate_category() -> list:
    return [{
        'title': 'Основная категория_' + get_random_string(length=4),
        'template': '<div>{{text}}</div>',
    }]


def generate_compiled_email(data_user: dict, event: int) -> list:
    return [{
        'title': 'Тестовый темплейт',
        'subject': f'Тестовый темплейт {data_user["email"]}',
        'text': f'Контент текстовый {data_user["email"]} - {some_text}',
        'html': f'Контент HTML {data_user["email"]} - {some_text}',
        'type': TYPE.EMAIL,
        'event': event,
    }]


def generate_compiled_viber(viber_chat_id: str, event: int) -> list:
    return [{
        'title': 'Тестовый темплейт вайбер',
        'subject': f'Тестовый темплейт {viber_chat_id}',
        'text': f'Контент текстовый {viber_chat_id} - {some_text}',
        'html': f'Контент HTML {viber_chat_id} - {some_text}',
        'type': TYPE.VIBER,
        'event': event,
    }]


def generate_notify_data(user) -> dict:
    test_data = {
        'sometext': some_text,
        'user': user
    }
    return test_data


def generate_system_notify_data() -> dict:
    return {f"{get_random_string(length=4)}": f"{get_random_string(length=7)}"}


def generate_system_template_data(value: dict, event: int) -> list:
    return [{
        'title': 'Тестовый системный темплейт',
        'subject': 'Тестовый темплейт',
        'text': value,
        'html': value,
        'type': TYPE.SYSTEM,
        'event': event,
    }]


def generate_compiled_system(value: dict, event: int, user) -> list:
    value['type'] = 'system'
    value['user'] = user.pk
    return [{
        "title": 'Тестовый темплейт',
        "data_json": value,
        "type": TYPE.SYSTEM,
        "event": event,
    }]


def generate_templates_views(event: int) -> list:
    return [{
        'title': 'Тестовый темплейт',
        'subject': 'Тестовый темплейт',
        'text': '{{message}} - {{confirmation_code}}',
        'html': '{{message}} - {{confirmation_code}}',
        'type': TYPE.EMAIL,
        'event': event,
    }]


def generate_compiled_email_views(event: int) -> list:
    return [{
        'title': 'Тестовый темплейт',
        'subject': 'Тестовый темплейт',
        'text': 'Привет, тут твое сообщение - abcdef12345',
        'html': 'Привет, тут твое сообщение - abcdef12345',
        'email': 'example@garpix.com',
        'type': TYPE.EMAIL,
        'event': event,
    }]
