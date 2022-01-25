# Garpix Notify


## Quickstart

Install with pip:

```bash
pip install garpix_notify
```

Add the `garpix_notify` and dependencies to your `INSTALLED_APPS`:

```python
# settings.py

INSTALLED_APPS = [
    # ...
    'fcm_django',
    'garpix_notify',
]

FCM_DJANGO_SETTINGS = {
        "APP_VERBOSE_NAME": "Firebase Cloud Messaging",
        "FCM_SERVER_KEY": "[your api key]",
        "ONE_DEVICE_PER_USER": False,
        "DELETE_INACTIVE_DEVICES": False,
}

NOTIFY_SMS_URL = "http://sms.ru/sms/send"
NOTIFY_SMS_API_ID = "[your api key from sms.ru]"


```

Package not included migrations, set path to migration directory. Don't forget create this directory (`app/migrations/garpix_notify/`) and place empty `__init__.py`:

```
app/migrations/
app/migrations/__init__.py  # empty file
app/migrations/garpix_notify/__init__.py  # empty file
```

Add path to settings:

```python
# settings.py

MIGRATION_MODULES = {
    'garpix_notify': 'app.migrations.garpix_notify',
}
```

Create your custom user model and add `AUTH_USER_MODEL` to `app/settings.py`:

```
AUTH_USER_MODEL = 'user.User'

```

Run make migrations:

```bash
python manage.py makemigrations
```

Migrate:

```bash
python manage.py migrate
```

### Example

#### Step 1. Set notify types in `app/settings.py`, for example:

```python
REGISTRATION_EVENT = 1
FEEDBACK_EVENT = 2
EXAMPLE_EVENT_1 = 3
EXAMPLE_EVENT_2 = 4


NOTIFY_EVENTS = {
    REGISTRATION_EVENT: {
        'title': 'Register',
    },
    FEEDBACK_EVENT: {
        'title': 'Feeback',
    },
    EXAMPLE_EVENT_1: {
        'title': 'Example 1',
    },
    EXAMPLE_EVENT_2: {
        'title': 'Example 2',
    },
}

CHOICES_NOTIFY_EVENT = [(k, v['title']) for k, v in NOTIFY_EVENTS.items()]

```

#### Step 2. Go to the admin panel and go to the "Notifications" section - "SMTP accounts"

Add an SMTP account to send Email notifications. These will be the senders of Email notifications.

#### Step 3. Also go to "Notifications" - "Categories"

Create a category that will be used to send emails. Usually one category is enough. The ability to enter several categories
is necessary to divide them into informational and marketing notifications.

#### Step 4. Go to "Notifications" - "Templates"

Create a template for a specific event (when you added them to `settings.py`).

#### Step 5. Call Notify.send()

In the code where it is necessary to work out sending a notification, we perform the following actions:

```python
from django.conf import settings
from garpix_notify.models import Notify

# Syntax
# Notify.send(<event>, <context>[, <user=None>, <email=None>, <phone=None>, <files=None>, <data_json=None>])
# That is, we specify the event ID as the first parameter,
# create variables for the template,
# third - the user to send it to (it is not necessary to specify his email, phone number, etc.,
# because this will be determined automatically depending on the type of template)

# Пример
user = request.user  # this will be the recipient of the notification.

Notify.send(settings.REGISTRATION_EVENT, {
    'confirmation_code': 'abcdef12345',
}, user=user)

# If we do not have a user in the system, but we need to send an email, we can do the following

Notify.send(settings.EXAMPLE_EVENT_1, {
    'confirmation_code': 'abcdef12345',
}, email='example@mail.ru')

```

Do not forget run celery:

```
celery -A app worker --loglevel=info -B
```

# Telegram Notify

Register you bot [https://t.me/BotFather](https://t.me/BotFather)

Go to [http://localhost:8000/admin/garpix_notify/notifyconfig/](https://t.me/BotFather) and fill "Telegram" section (`API key` and `Bot name`).

Run daemon:

```bash
python3 backend/manage.py garpix_notify_telegram
```

Go to your bot and send `/start` command.

Also, see `user/admin.py` file (see instructions):

```python
from django.contrib import admin
from .models import User
from django.contrib.auth.admin import UserAdmin


@admin.register(User)
class UserAdmin(UserAdmin):
    fieldsets = (
        ('Telegram', {
            'fields': ('telegram_chat_id', 'telegram_secret', 'get_telegram_connect_user_help'),
        })
    ) + UserAdmin.fieldsets
    readonly_fields = ['telegram_secret', 'get_telegram_connect_user_help'] + list(UserAdmin.readonly_fields)
```

# System ws Notify

Add the `channels` to your `INSTALLED_APPS`:

```python
# settings.py

INSTALLED_APPS = [
    # ...
    'channels',
]
```

Add the `REDIS_HOST` and `REDIS_PORT` variables and `asgi` and `channels` configurations:

```python
# settings.py

REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = os.getenv('REDIS_PORT', 6379)

...

ASGI_APPLICATION = 'app.asgi.application'
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [(REDIS_HOST, REDIS_PORT)],
        },
    },
}
```

Edit your `asgi.py` file

```python
import os
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from garpix_notify import routing


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')

application = ProtocolTypeRouter({
  "http": get_asgi_application(),
  "websocket": AuthMiddlewareStack(
        URLRouter(
            routing.websocket_urlpatterns
        )
    ),
})
```

Socket notification example

```python
group_name = f'workflow-{user.pk}'
Notify.send(settings.MY_NOTIFY, {
        'message': 'my message',
    }, room_name=group_name, user=user)
```

For notifications of the SYSTEM type, a separate non-periodic task is used that works instantly, if room_name is missing system messages will be sent in `'room_{id}'` where `'id'` is user id

# Changelog

See [CHANGELOG.md](CHANGELOG.md).

# Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

# License

[MIT](LICENSE)
