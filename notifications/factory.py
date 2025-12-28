from .models import Notification
from notifications.blueprints import *
from notifications.constants.notification_types import *


class NotificationFactory:
    """Factory for creating notifications with appropriate templates"""

    _templates = {
        # Notification type: Blueprint class
        # Example:
        # NEW_FOLLOWER: NewFollowerBlueprint,
    }

    @classmethod
    def get_template(cls, notification):
        """Get the appropriate template for a notification"""
        template_class = cls._templates.get(notification.type)
        if not template_class:
            raise ValueError(
                f"No template found for notification type: {notification.type}"
            )
        return template_class(notification)

    @classmethod
    def create_notification(cls, user, type, data=None):
        """Create a new notification"""
        return Notification.objects.create(
            user=user,
            type=type,
            data=data or {},
        )
