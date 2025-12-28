from celery import shared_task
from notifications.models import EmailLog, Notification
from django.utils import timezone
from datetime import timedelta


@shared_task
def clean_up_notifications():
    # Delete email logs older than 14 days
    EmailLog.objects.filter(sent_at__lt=timezone.now() - timedelta(days=14)).delete()

    # Delete notifications older than 60 days that are read
    Notification.objects.filter(
        created_at__lt=timezone.now() - timedelta(days=60), is_read=True
    ).delete()

    # Delete notifications older than 90 days that are not read
    Notification.objects.filter(
        created_at__lt=timezone.now() - timedelta(days=90), is_read=False
    ).delete()
