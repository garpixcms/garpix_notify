from django.core.mail.backends.smtp import EmailBackend as DjangoEmailBackend
from garpix_notify.models.smtp import SMTPAccount

try:
    smtp = SMTPAccount.get_free_smtp()
except Exception as e:
    raise ("[SMTPAccount not found] Проверьте настроки в админке : /admin/garpix_notify/smtpaccount/", e)


class EmailBackend(DjangoEmailBackend):

    def __init__(self, host=smtp.host, port=smtp.port, username=smtp.sender, password=smtp.password,
                 use_tls=smtp.is_use_tls, fail_silently=False, use_ssl=smtp.is_use_ssl, timeout=None,
                 ssl_keyfile=None, ssl_certfile=None, **kwargs):
        super().__init__(host, port, username, password, use_tls, fail_silently, use_ssl, timeout,
                         ssl_keyfile, ssl_certfile, **kwargs)
