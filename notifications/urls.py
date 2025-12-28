from django.urls import path, include
from rest_framework import routers
from .api import *

push_router = routers.DefaultRouter()
push_router.register(r"", PushSubscriptionViewSet, basename="push-subscriptions")

notification_routes = [
    path("", NotificationView.as_view(), name="notifications"),
    path(
        "settings/",
        NotificationSettingsView.as_view(),
        name="notification-settings",
    ),
    path(
        "unsubscribe-emails/",
        UnsubscribeFromEmailView.as_view(),
        name="unsubscribe-emails",
    ),
]

urlpatterns = [
    path("push/", include(push_router.urls)),
    path("zeptomail/", ZeptoMailWebhookView.as_view(), name="zeptomail-webhook"),
    path("", include(notification_routes)),
]
