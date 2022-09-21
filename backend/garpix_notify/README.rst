
Garpix Notify
=============

Quickstart
----------

Install with pip:


.. code-block:: bash

   pip install garpix_notify

Add the ``garpix_notify`` and dependencies to your ``INSTALLED_APPS``\ :

.. code-block:: python

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

Package not included migrations, set path to migration directory. Don't forget create this directory (\ ``app/migrations/garpix_notify/``\ ) and place empty ``__init__.py``\ :

.. code-block::

   app/migrations/
   app/migrations/__init__.py  # empty file
   app/migrations/garpix_notify/__init__.py  # empty file

Add path to settings:

.. code-block:: python

   # settings.py

   MIGRATION_MODULES = {
       'garpix_notify': 'app.migrations.garpix_notify',
   }


Add mixins to settings if you need to add extra functionality to Notify models:

.. code-block::

    # settings.py

    GARPIX_NOTIFY_MIXIN = 'app.models.notify_mixin.NotifyMixin'
    GARPIX_SYSTEM_NOTIFY_MIXIN = 'app.models.notify_mixin.SystemNotifyMixin'


Create your custom user model and add ``AUTH_USER_MODEL`` to ``app/settings.py``\ :

.. code-block::

   AUTH_USER_MODEL = 'user.User'

Run make migrations:

.. code-block:: bash

   python manage.py makemigrations

Migrate:

.. code-block:: bash

   python manage.py migrate

Example
^^^^^^^

Step 1. Set notify types in ``app/settings.py``\ , for example:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

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

Step 2. Import default settings in your ``app/settings.py``\
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
.. code-block:: python

    from garpix_notify.settings import *


or copy from here if you want more customization


.. code-block:: python
    PERIODIC_SENDING = 60
    EMAIL_MAX_DAY_LIMIT = 240
    EMAIL_MAX_HOUR_LIMIT = 240
    # SMS
    SMS_URL_TYPE = 0
    SMS_API_ID = 1234567890
    SMS_LOGIN = ''
    SMS_PASSWORD = ''
    SMS_FROM = ''
    # CALL
    CALL_URL_TYPE = 0
    CALL_API_ID = 1234567890
    CALL_LOGIN = ''
    CALL_PASSWORD = ''
    # TELEGRAM
    TELEGRAM_API_KEY = '000000000:AAAAAAAAAA-AAAAAAAA-_AAAAAAAAAAAAAA'
    TELEGRAM_BOT_NAME = 'MySuperBot'
    TELEGRAM_WELCOME_TEXT = 'Hello'
    TELEGRAM_HELP_TEXT = '/set !help for HELP'
    TELEGRAM_BAD_COMMAND_TEXT = 'Incorrect command format'
    TELEGRAM_SUCCESS_ADDED_TEXT = 'Success'
    TELEGRAM_FAILED_ADDED_TEXT = 'Failed'
    TELEGRAM_PARSE_MODE = None
    TELEGRAM_DISABLE_NOTIFICATION = False
    TELEGRAM_DISABLE_PAGE_PREVIEW = False
    TELEGRAM_SENDING_WITHOUT_REPLY = False
    TELEGRAM_TIMEOUT = None
    # VIBER
    VIBER_API_KEY = '000000000:AAAAAAAAAA-AAAAAAAA-_AAAAAAAAAAAAAA'
    VIBER_BOT_NAME = 'MySuperViberBot'
    VIBER_WELCOME_TEXT = 'Hello'
    VIBER_SUCCESS_ADDED_TEXT = 'Success'
    VIBER_FAILED_ADDED_TEXT = 'Failed'
    VIBER_TEXT_FOR_NEW_SUB = 'HI!'
    # WHATSAPP
    IS_WHATS_APP_ENABLED = True
    WHATS_APP_AUTH_TOKEN = None
    WHATS_APP_ACCOUNT_SID = None
    WHATS_APP_NUMBER_SENDER = None
    # SETTINGS
    EMAIL_MALLING = 1
    GARPIX_NOTIFY_MIXIN = 'garpix_notify.mixins.notify_mixin.NotifyMixin'
    NOTIFY_USER_WANT_MESSAGE_CHECK = None
    NOTIFY_CALL_CODE_CHECK = None
    GARPIX_NOTIFY_CELERY_SETTINGS = 'app.celery.app'


Step 3. Go to the admin panel and go to the "Notifications" section - "SMTP accounts"
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Add an SMTP account to send Email notifications. These will be the senders of Email notifications.

Step 4. Also go to "Notifications" - "Categories"
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Create a category that will be used to send emails. Usually one category is enough. The ability to enter several categories
is necessary to divide them into informational and marketing notifications.

Step 5. Go to "Notifications" - "Templates"
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Create a template for a specific event (when you added them to ``settings.py``\ ).

Step 5. Call Notify.send()
~~~~~~~~~~~~~~~~~~~~~~~~~~

In the code where it is necessary to work out sending a notification, we perform the following actions:

.. code-block:: python

   from django.conf import settings
   from garpix_notify.models import Notify

   # Syntax
   # Notify.send(<event>, <context>[, <user=None>, <email=None>, <phone=None>, <files=None>, <data_json=None>])
   # That is, we specify the event ID as the first parameter,
   # create variables for the template,
   # third - the user to send it to (it is not necessary to specify his email, phone number, etc.,
   # because this will be determined automatically depending on the type of template)

   # Example
   user = request.user  # this will be the recipient of the notification.

   Notify.send(settings.REGISTRATION_EVENT, {
       'confirmation_code': 'abcdef12345',
   }, user=user)

   # If we do not have a user in the system, but we need to send an email, we can do the following

   Notify.send(settings.EXAMPLE_EVENT_1, {
       'confirmation_code': 'abcdef12345',
   }, email='example@mail.ru')

   # If you need more detailed time settings, add send_at
   Notify.send(settings.EXAMPLE_EVENT_1, {
       'confirmation_code': 'abcdef12345',
   }, email='example@mail.ru', send_at=(datetime.datetime.now() + datetime.timedelta(days=1)))

   # If you need to send a code by phone call
   Notify.send(settings.EXAMPLE_EVENT_2, phone='79998881122')

   # or if you need to get the code directly
   Notify.call(phone=79998881122)

   # If you need to send a system message without creating a template, you must specify the system=True
    Notify.send(settings.EXAMPLE_EVENT_1, {
        'confirmation_code': 'abcdef12345',
    }, user=user, system=True)

Mass email mailing
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
To perform a mass mailing, you need to add user lists to the template.
Or directly in the notification.

Do not forget run celery:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
.. code-block::

   celery -A app worker --loglevel=info -B

Changelog
=========

See `CHANGELOG.md <CHANGELOG.md>`_.

Contributing
============

See `CONTRIBUTING.md <CONTRIBUTING.md>`_.

License
=======

`MIT <LICENSE>`_
