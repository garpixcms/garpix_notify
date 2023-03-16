### 5.14.0 (16.03.2023)
- System notifies view added (see `Readme.md`)
- `is_read` field added to `SystemNotify`.

### 5.13.6 (30.11.2022)
- For the operator `web.szk-info.ru` fixed OK answer, the request is now sent over https.
- For the `web.szk-info.ru` operator, all the necessary fields are displayed in the admin panel.
- Now you can send test notifications from the template for: SMS, CALL, EMAIL, PUSH.

### 5.13.5 (21.11.2022)
- For the operator `web.szk-info.ru` fixed answers.

### 5.13.4 (16.11.2022)
- Fixed the error of incorrect URL.

### 5.13.3 (13.10.2022)
- In the administrative panel, the work of selecting a telecom provider has been corrected.

### 5.13.2 (10.10.2022)
- User is now `row_id_field` in `NotifyTemplateAdmin`

### 5.13.1 (05.10.2022)
- In SystemNotify, the `event_id key` is corrected to `event`,
- In the Admin panel in the notification templates, a button has been added to launch a test SystemNotify.

### 5.13.0 (03.10.2022)
- Added `Delete after send` checkbox to notify template (deletes notify and it's files).

### 5.12.5 (28.09.2022)
- Added a warning in the admin panel that there are events without templates,
- Removed the exception that no templates were found from the send method.

### 5.12.4 (27.09.2022)
- An email with html, text and attachments is now formed correctly.

### 5.12.1-5.12.3 (26.09.2022)
- Returned NotifyMethodsMixin.

### 5.12.0 (24.09.2022)

- Now you need to specify the parameter user_want_message_check in Notify.send() ,
- Improved performance, as well as the structure of the application,
- Minor bugs fixed,
- Redesigned tests.

### 5.11.6 (22.09.2022)

- Fixed bug with sms client config

### 5.11.5 (21.09.2022)

- Default mixins to Notify models added

### 5.11.4 (19.09.2022)

- Fixed bugs with phone field and sms client config


### 5.11.3 (24.08.2022)

SystemNotify:
- Fixed a bug with a JSONField with Cyrillic,
- More correct generation of data for sending.

### 5.11.2 (21.08.2022)

- The data_json field in the SystemNotify model is JSONField.

### 5.11.1 (21.08.2022)

- Corrected tests for new functionality.

### 5.11.0 (27.07.2022)

- Fixed a bug with the formation of users for mailing,
- The 'Mailing list of users' can now be filled in by users or groups,
- The message can be sent instantly by passing the send_now parameter,
- System notifications have been added separately.

### 5.10.1 (05.07.2022)

- Fixed a critical bug, the ban on sending email did not work,
- Corrected Readme,
- Now the asgiref library is installed correctly.

### 5.10.0 (04.07.2022)

- Updated asgiref library to version 3.3.4,
- Added support for WhatsApp (Twilio),
- System notifications no longer need a template,
- Fixed a bug with the formation of a list of recipients.

### 5.9.0 (29.06.2022)

- Django==3.2

### 5.8.0 (07.06.2022)

- Added the Call method (Notify.call(phone, user, url, **kwargs)),
- Fix bugs,
- Fixed work NOTIFY_USER_WANT_MESSAGE_CHECK,
- New settings for Telegram,
- Telecom operators added.

### 5.7.0 (01.06.2022)

- Added support for calls from SMS_RU.
- Fixing critical bugs

### 5.6.3 (01.06.2022)

- Fixed response from SMS_RU.

### 5.6.2 (30.05.2022)

- Fixed path to Celery tasks.

### 5.6.1 (19.05.2022)

- Fixed path to NotifyMixin.

### 5.6.0 (19.05.2022)

- Customizing NotifyMixin added.

### 5.5.0 (10.05.2022)

- Added the possibility of mass mailing,
- Telecom operators added,
- Fixed bugs.

### 5.4.2 (06.05.2022)

- In "system" notifications, the id of this notification is additionally received

### 5.4.1 (04.04.2022)

- Fixed version issue with existing projects

### 5.4.0 (01.04.2022)

- Added support for WEBSZK.

### 5.3.3 (11.03.2022)

- When creating "System" notifications, the function will be called only when records in the database are committed
- In "system" notifications, the event of this notification is additionally received

### 5.3.2 (22.02.2022)

- Fixed a bug that changed the status of System notifications

### 5.3.1 (16.02.2022)

- Fix user circular import error.

### 5.3.0 (02.02.2022)

- for notifications of the SYSTEM type, a separate non-periodic task is added

### 5.2.0 (20.01.2022)

- room_name field added to Notify model

### 5.1.0-5.1.2 (11.01.2022)

- Fixed bug with email sending limits

### 5.0.0 (29.10.2021)

- Added system notify (websockets).

### 4.1.0 (02.08.2021)

- Telegram models, daemon.

### 4.0.2 (02.08.2021)

- Fixed beat_schedule.

### 4.0.1 (27.08.2021)

- Fixed bug sending messages

### 4.0.0 (12.08.2021)

- Added the ability to send notifications with only email
- Upgraded to 5 version of `celery`.

### 3.0.3 (12.07.2021)

- Switch to legacy `fcm-django`.

### 3.0.2 (02.07.2021)

- Fixed bug with send email notifications.

### 3.0.1 (28.06.2021)

- Fixed bug with celery version.

### 3.0.0 (28.06.2021)

- First release in pypi.org.
