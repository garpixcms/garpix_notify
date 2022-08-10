from django.utils.html import format_html

from garpix_notify.models.system_log import SystemNotifyErrorLog
from garpix_notify.models.log import NotifyErrorLog
from garpix_notify.models.choices import STATE


class NotifyMethodsMixin:

    def get_format_state(self):
        if self.state == STATE.WAIT:
            return format_html('<span style="color:orange;">В ожидании</span>')
        elif self.state == STATE.DELIVERED:
            return format_html('<span style="color:green;">Отправлено</span>')
        elif self.state == STATE.REJECTED:
            return format_html('<span style="color:red;">Отклонено</span>')
        elif self.state == STATE.DISABLED:
            return format_html('<span style="color:red;">Отправка запрещена</span>')
        return format_html('<span style="color:black;">Неизвестный статус</span>')

    get_format_state.short_description = 'Статус'

    def to_log(self, error_text):
        from garpix_notify.models.notify import Notify
        if isinstance(self, Notify):
            log = NotifyErrorLog(notify=self, error=error_text)
        else:
            log = SystemNotifyErrorLog(notify=self, error=error_text)
        log.save()
