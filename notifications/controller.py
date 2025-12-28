import logging
from notifications.factory import NotificationFactory
from notifications.models import UserNotificationSettings
from notifications.emails import *
from notifications.services.push_notifications import push_notification_to_user
from notifications.constants.notification_channels import *
from notifications.constants.notification_types import *
from django.conf import settings as django_settings

logger = logging.getLogger(__name__)


class NotificationsController:
    def __init__(self):
        pass

    def notify_user(self, user, notification_type, data=None):
        """
        Centralized function to notify a user across all channels.
        """
        sent_data = {"email": False, "push": False}

        if user:
            try:
                settings = UserNotificationSettings.objects.get(user=user)
            except UserNotificationSettings.DoesNotExist:
                logger.warning(f"No notification settings found for user: {user.email}")
                return sent_data

            # Create the notification
            notification = NotificationFactory.create_notification(
                user=user,
                type=notification_type,
                data=data or {},
            )

            # Get the template
            template = NotificationFactory.get_template(notification)

            settings_key = NOTIFICATION_TYPE_SETTINGS_MAP.get(notification_type, None)
            preference = (
                getattr(settings, settings_key, "NONE") if settings_key else "NONE"
            )

        else:
            raise ValueError("No user provided")

        template_channels = template.get_channels()

        # Send email if needed
        if (
            preference in [EMAIL, ALL]
            and EMAIL in template_channels
            and user.is_email_valid
            and template.should_send_email()
        ):
            email_sent = self._send_email(notification_type, template, notification)
            sent_data["email"] = email_sent

        # Send push if needed
        if preference in [PUSH, ALL] and PUSH in template_channels:
            push_sent = self._send_push(notification, template)
            sent_data["push"] = push_sent

        return notification, sent_data

    def _send_email(self, notification_type, template, notification):
        """Send email notification"""
        # Get the appropriate email function based on notification type
        if not self._should_send_notification(notification):
            return False

        email_function = template.get_email_function()
        if not email_function:
            logger.warning(
                f"No email function found for notification type: {notification_type}"
            )
            return False

        # Send the email
        email_sent = False
        try:
            email_function(template.get_email_context())
            email_sent = True
        except Exception as e:
            email_sent = False

        # Mark as delivered
        if notification:
            notification.delivered_email = email_sent
            notification.save(update_fields=["delivered_email"])

        return email_sent

    def _send_push(self, notification, template):
        """Send push notification"""
        if not self._should_send_notification(notification):
            return False

        push_sent = push_notification_to_user(
            notification.user,
            template.get_title(),
            template.get_body(),
            data=template.get_push_data(),
        )

        # Mark as delivered
        notification.delivered_push = push_sent
        notification.save(update_fields=["delivered_push"])

        return push_sent

    def _should_send_notification(self, notification):
        if django_settings.ENVIRONMENT != "production":
            if (
                not notification.user.email in django_settings.DEV_NOTIFICATIONS
                or "pkundr.com" in notification.user.email
            ):
                return False
        return True
