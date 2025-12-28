import os
import json
from django.conf import settings
import firebase_admin
from firebase_admin import credentials, messaging
from django.conf import settings
from notifications.models import PushSubscription
from django.utils import timezone

if not settings.DEBUG:
    CREDENTIALS_FILE = os.path.join(
        settings.BASE_DIR,
        f"credentials/fcm-service-credentials-{settings.ENVIRONMENT}.json",
    )

if not firebase_admin._apps and not settings.DEBUG:
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
        return False

    push_subscriptions = PushSubscription.objects.filter(user=user)
    if not push_subscriptions.exists():
        print(f"No push subscriptions found for {user.email}")
        return False

    print(
        f"Sending notification to {user.email} with {push_subscriptions.count()} subscriptions"
    )

    for push_subscription in push_subscriptions:
        success = send_push_notification(
            token=push_subscription.fcm_token,
            title=title,
            body=body,
            data=data,
            actions=actions,
        )

        if success:
            push_subscription.last_successful_send = timezone.now()
            push_subscription.save()

    return True


def send_push_notification(token, title, body, data=None, actions=None):
    """
    Sends a single push notification via Firebase Cloud Messaging.

    --> Do not call this directly, use push_notification_to_user instead.
    """

    try:
        notification_data = data or {}
        if actions:
            notification_data["actions"] = json.dumps(actions)

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
            data={
                **{k: str(v) for k, v in notification_data.items()},
                "url": target_url,
            },
            token=token,
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
                        content_available=1,
                        mutable_content=1,
                    ),
                    custom_data={"url": target_url, **notification_data},
                ),
            ),
        )

        messaging.send(message)
        return True
    except messaging.UnregisteredError:
        # Token is no longer valid (app uninstalled or token expired)
        print(f"Token {token} is no longer valid, deleting subscription")
        PushSubscription.objects.filter(fcm_token=token).delete()
        return False
    except messaging.QuotaExceededError:
        # Don't delete subscription - this is a temporary issue
        print(f"Quota exceeded for FCM")
        return False
    except messaging.ThirdPartyAuthError:
        # Don't delete - this is a configuration issue
        print(f"FCM authentication error")
        return False
    except messaging.SenderIdMismatchError:
        # Token was generated with different sender
        print(f"Token {token} was created for different sender, deleting subscription")
        PushSubscription.objects.filter(fcm_token=token).delete()
        return False
    except Exception as e:
        # For unknown errors, log but don't delete
        print(f"Unknown error sending message to {token}: {str(e)}")
        return False
