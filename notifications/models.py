from django.db import models
from core.models import BaseModel
from notifications.constants.notification_types import *


class EmailLog(models.Model):

    email = models.EmailField()
    type = models.CharField(max_length=255)
    sent_at = models.DateTimeField(auto_now_add=True)
    reference_id = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.email} - {self.type} - {self.sent_at}"


class PushSubscription(BaseModel):
    class Platform(models.TextChoices):
        ANDROID = "ANDROID", "Android"
        IOS = "IOS", "IOS"
        WEB = "WEB", "Web"

    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="push_subscriptions",
    )
    fcm_token = models.CharField(max_length=255, unique=True)
    platform = models.CharField(
        max_length=255, choices=Platform.choices, null=True, blank=True
    )
    last_successful_send = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.email} - {self.fcm_token}"


class UserNotificationSettings(BaseModel):

    class Preferences(models.TextChoices):
        EMAIL = "EMAIL", "Email"
        PUSH = "PUSH", "Push"
        ALL = "ALL", "All"
        NONE = "NONE", "None"

    class Meta:
        verbose_name = "User Notification Settings"
        verbose_name_plural = "User Notification Settings"

    user = models.OneToOneField(
        "users.User",
        on_delete=models.CASCADE,
        related_name="notification_settings",
    )


class Notification(BaseModel):
    """
    Unified notification model that can represent any type of notification.
    """

    TYPE_CHOICES = ()

    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="notifications_old",
    )
    type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    is_read = models.BooleanField(default=False)

    # Store additional data as JSON
    data = models.JSONField(default=dict, blank=True)

    # Track delivery status across channels
    delivered_in_app = models.BooleanField(default=True)
    delivered_email = models.BooleanField(default=False)
    delivered_push = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "type", "is_read"]),
        ]

    def __str__(self):
        return f"{self.type} Notification for {self.user.username}"
