import os
import json
import firebase_admin
from firebase_admin import credentials, messaging
from django.conf import settings
from users.models import PushSubscription

CREDENTIALS_FILE = os.path.join(
    settings.BASE_DIR,
    f"credentials/fcm-service-credentials-{settings.ENVIRONMENT}.json",
)

if not firebase_admin._apps:
    cred = credentials.Certificate(CREDENTIALS_FILE)
    firebase_admin.initialize_app(cred, {"vapid_key": settings.VAPID_PRIVATE_KEY})


def push_notification_to_user(user, title, body, data=None, actions=None):
    """
    Retrieves the user's push token(s) and sends a notification.
    In development, only sends to staff users.
    """
    # Check if in development and user is not staff
    if (
        settings.ENVIRONMENT != "production"
        and not user.email in settings.DEV_NOTIFICATIONS
    ):
        print(f"Not sending notification to {user.email} in development")
        return

    push_subscriptions = PushSubscription.objects.filter(user=user)
    if not push_subscriptions.exists():
        print(f"No push subscriptions found for {user.email}")
        return

    print(
        f"Sending notification to {user.email} with {push_subscriptions.count()} subscriptions"
    )

    for push_subscription in push_subscriptions:
        send_push_notification(
            token=push_subscription.fcm_token,
            title=title,
            body=body,
            data=data,
            actions=actions,
        )


def send_push_notification(token, title, body, data=None, actions=None):
    """
    Sends a single push notification via Firebase Cloud Messaging.

    --> Do not call this directly, use push_notification_to_user instead.
    """

    try:
        notification_data = data or {}
        if actions:
            notification_data["actions"] = json.dumps(actions)

        # Get the target URL, defaulting to app home
        target_url = (
            notification_data.get("url", settings.APP_URL)
            if notification_data
            else settings.APP_URL
        )

        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data=notification_data,
            token=token,
            # Web configuration
            webpush=messaging.WebpushConfig(
                notification=messaging.WebpushNotification(
                    icon="/icons/pwa-maskable-192x192.png",
                    badge="/icons/favicon-32x32.png",
                ),
                headers={"Urgency": "high"},
                fcm_options=messaging.WebpushFCMOptions(link=target_url),
            ),
            # iOS configuration
            apns=messaging.APNSConfig(
                headers={
                    "apns-priority": "10",
                },
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(
                        alert=messaging.ApsAlert(
                            title=title,
                            body=body,
                        ),
                        sound="default",
                        badge=1,
                    ),
                    # Include the URL in both places for iOS
                    fcm_options={"link": target_url},
                    data={"url": target_url},
                ),
            ),
        )

        messaging.send(message)
        return True
    except Exception as e:
        print(f"Error sending message to {token}: {str(e)}")
        subs = PushSubscription.objects.filter(fcm_token=token)
        if subs.exists():
            print(f"Deleting expired subscriptions")
            subs.delete()

        return False
