def send_notify_now_async(notify_pk):
    """Постановка уведомления в очередь Celery для немедленной отправки."""
    from garpix_notify.tasks.tasks import send_notify_now
    send_notify_now.delay(notify_pk)
