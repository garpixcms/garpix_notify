
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

Step 2. Go to the admin panel and go to the "Notifications" section - "SMTP accounts"
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Add an SMTP account to send Email notifications. These will be the senders of Email notifications.

Step 3. Also go to "Notifications" - "Categories"
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Create a category that will be used to send emails. Usually one category is enough. The ability to enter several categories
is necessary to divide them into informational and marketing notifications.

Step 4. Go to "Notifications" - "Templates"
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

   # Пример
   user = request.user  # this will be the recipient of the notification.

   Notify(settings.REGISTRATION_EVENT, {
       'confirmation_code': 'abcdef12345',
   }, user=user)

   # If we do not have a user in the system, but we need to send an email, we can do the following

   Notify(settings.EXAMPLE_EVENT_1, {
       'confirmation_code': 'abcdef12345',
   }, email='example@mail.ru')

Do not forget run celery:

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
