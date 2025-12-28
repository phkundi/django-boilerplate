from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.conf import settings as django_settings
from users.models import User
from notifications.models import (
    PushSubscription,
    UserNotificationSettings,
    Notification,
)
from notifications.services import (
    get_user_notification_settings,
    send_push_notification,
)
from notifications.serializers import PushSubscriptionSerializer, NotificationSerializer
from notifications.constants.notification_types import NOTIFICATION_TYPE_SETTINGS_MAP
from notifications.factory import NotificationFactory
from django.conf import settings as django_settings
import logging
import hmac
import hashlib
import base64
import time
from urllib.parse import unquote
import json

logger = logging.getLogger(__name__)


class PushSubscriptionViewSet(viewsets.GenericViewSet):
    serializer_class = PushSubscriptionSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        try:
            existing_subscription = PushSubscription.objects.filter(
                user=request.user, fcm_token=request.data.get("fcm_token")
            ).first()

            if existing_subscription:
                return Response(
                    {"message": "Push subscription already exists"},
                    status=status.HTTP_200_OK,
                )

            platform = request.data.get("platform", None)
            if platform:
                platform = platform.upper()

            subscription, _ = PushSubscription.objects.get_or_create(
                user=request.user,
                fcm_token=request.data.get("fcm_token"),
                platform=platform,
            )
            serializer = self.get_serializer(subscription)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            # print(e)
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def destroy(self, request, *args, **kwargs):
        try:
            PushSubscription.objects.filter(user=request.user).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=["post"], url_path="test-notification")
    def test_notification(self, request):
        try:
            subscription = PushSubscription.objects.filter(user=request.user)
            if not subscription.exists():
                return Response(
                    {"error": "No push subscription found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            sent = []
            for sub in subscription:
                result = send_push_notification(
                    sub.fcm_token,
                    request.data.get("title", "Test Notification"),
                    request.data.get("body", "This is a test notification"),
                    data={
                        "url": f"{django_settings.APP_URL}/profile/{sub.user.username}",
                        "type": "test",
                    },  # Add custom data
                )

                if result:
                    sent.append(sub.fcm_token)
            if len(sent) > 0:
                return Response({"message": "Notification sent successfully"})
            else:
                return Response(
                    {"error": "Failed to send notification"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
        except Exception as e:
            logger.error(f"Error in test_notification: {str(e)}")
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class NotificationSettingsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            return Response(
                get_user_notification_settings(request.user),
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def put(self, request):
        try:
            settings = UserNotificationSettings.objects.get(user=request.user)
            update_field = request.data.get("update_field")
            update_value = request.data.get("update_value")
            setattr(settings, update_field, update_value)
            settings.save()
            return Response(status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UnsubscribeFromEmailView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            email = request.data.get("email")
            email_type = request.data.get("email_type")

            user = User.objects.filter(email=email).first()

            if not user:
                return Response("User not found", status=status.HTTP_404_NOT_FOUND)

            setting_key = NOTIFICATION_TYPE_SETTINGS_MAP.get(email_type, None)
            if not setting_key:
                return Response(
                    "Can't unsubscribe from this email type",
                    status=status.HTTP_200_OK,
                )

            user_settings = UserNotificationSettings.objects.get(user=user)
            current_setting = getattr(user_settings, setting_key, "NONE")

            if current_setting == "ALL":
                new_value = "PUSH"
            elif current_setting == "EMAIL":
                new_value = "NONE"
            else:
                new_value = "NONE"

            setattr(user_settings, setting_key, new_value)
            user_settings.save()

            return Response("Unsubscribed from email type", status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class NotificationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user:
            return Response("User not found", status=status.HTTP_404_NOT_FOUND)

        # Fetch notifications with user prefetched
        queryset = (
            Notification.objects.filter(user=request.user)
            .select_related("user")
            .order_by("-created_at")
        )

        # Convert to list to allow iteration multiple times
        notifications_list = list(queryset)

        channel = request.query_params.get("channel")

        formatted_notifications = []
        for notification in notifications_list:
            try:
                template = NotificationFactory.get_template(notification)

                if channel and channel not in template.get_channels():
                    continue

                if request.query_params.get("unread") and notification.is_read:
                    continue

                serializer = NotificationSerializer(
                    notification, context={"template": template}
                )
                formatted_notifications.append(serializer.data)
            except Exception as e:
                import traceback

                logger.error(
                    f"Error formatting notification {notification.id} ({notification.type}): {str(e)}",
                    exc_info=traceback.format_exc(),
                )
                notification.delete()
                continue

        if request.query_params.get("limit"):
            formatted_notifications = formatted_notifications[
                : int(request.query_params.get("limit"))
            ]

        return Response(formatted_notifications, status=status.HTTP_200_OK)

    def patch(self, request):
        if not request.user:
            return Response("User not found", status=status.HTTP_404_NOT_FOUND)

        notification_id = request.data.get("notification_id")

        try:
            notification = Notification.objects.get(
                id=notification_id, user=request.user
            )
            notification.is_read = True
            notification.save()
            return Response("Notification marked as read", status=status.HTTP_200_OK)
        except Notification.DoesNotExist:
            return Response("Notification not found", status=status.HTTP_404_NOT_FOUND)

    def delete(self, request):
        if not request.user:
            return Response("User not found", status=status.HTTP_404_NOT_FOUND)

        notification_id = request.query_params.get("notification_id")

        try:
            notification = Notification.objects.get(
                id=notification_id, user=request.user
            )
            notification.delete()
            return Response("Notification deleted", status=status.HTTP_200_OK)
        except Notification.DoesNotExist:
            return Response("Notification not found", status=status.HTTP_404_NOT_FOUND)


@method_decorator(csrf_exempt, name="dispatch")
class ZeptoMailWebhookView(APIView):
    permission_classes = [AllowAny]

    def _verify_signature(self, request):
        """
        Verify ZeptoMail webhook HMAC signature.
        Based on ZeptoMail's official Java implementation.
        Returns (is_valid, data_json) tuple.
        """
        secret_key = getattr(django_settings, "ZEPTOMAIL_WEBHOOK_SECRET", None)
        if not secret_key:
            logger.warning(
                "ZEPTOMAIL_WEBHOOK_SECRET not configured, skipping signature verification"
            )
            return True, None

        producer_signature = request.headers.get("producer-signature")
        if not producer_signature:
            logger.warning("Missing producer-signature header")
            return False, None

        # URL decode and parse the signature header
        # Format: ts=<timestamp>;s-algorithm=<algorithm>;s=<signature>
        ps_decoded = unquote(producer_signature)
        sign_parts = ps_decoded.split(";")

        sign_data = {}
        for part in sign_parts:
            if "=" in part:
                key, value = part.split("=", 1)
                sign_data[key] = value

        # Check timestamp to prevent replay attacks (5 minute window)
        try:
            time_sent = int(sign_data.get("ts", 0))
            current_time = int(time.time() * 1000)  # milliseconds
            diff = current_time - time_sent
            acceptable_limit = 300000  # 5 minutes in milliseconds

            if diff > acceptable_limit:
                logger.warning(f"ZeptoMail webhook timestamp too old: {diff}ms")
                return False, None
        except (ValueError, TypeError):
            logger.warning("Invalid ZeptoMail timestamp format")
            return False, None

        # Get signature info
        signature_algorithm = sign_data.get("s-algorithm", "HmacSHA256")
        signature_received = sign_data.get("s")

        if not signature_received:
            logger.warning("Missing signature in producer-signature header")
            return False, None

        # Get request body and extract data value
        # Body format: data=<url-encoded-json>
        raw_body = request.body.decode("utf-8")
        body_decoded = unquote(raw_body)

        # Extract JSON from "data=<json>" format
        if "=" in body_decoded:
            data_value = body_decoded.split("=", 1)[1]
        else:
            data_value = body_decoded

        # Map Java algorithm name to Python hashlib
        algorithm_map = {
            "HmacSHA256": hashlib.sha256,
            "HmacSHA1": hashlib.sha1,
            "HmacSHA512": hashlib.sha512,
        }

        hash_func = algorithm_map.get(signature_algorithm, hashlib.sha256)

        # Calculate signature
        if isinstance(secret_key, str):
            secret_key_bytes = secret_key.encode("utf-8")
        else:
            secret_key_bytes = secret_key

        hmac_digest = hmac.new(
            key=secret_key_bytes,
            msg=data_value.encode("utf-8"),
            digestmod=hash_func,
        ).digest()

        calculated_signature = base64.b64encode(hmac_digest).decode()

        # Base64 decode both and compare (as per Java implementation)
        try:
            decode1 = base64.b64decode(signature_received)
            decode2 = base64.b64decode(calculated_signature)
        except Exception as e:
            logger.warning(f"Failed to decode signatures: {e}")
            return False, None

        is_valid = hmac.compare_digest(decode1, decode2)

        if is_valid:
            # Return parsed JSON data
            try:
                return True, json.loads(data_value)
            except json.JSONDecodeError:
                logger.warning("Failed to parse webhook JSON data")
                return False, None

        return False, None

    def post(self, request, *args, **kwargs):
        # Verify HMAC signature
        is_valid, data = self._verify_signature(request)
        if not is_valid:
            logger.warning("Invalid ZeptoMail webhook signature")
            return Response(
                {"status": "ok", "message": "Invalid signature"},
                status=status.HTTP_200_OK,
            )

        # Use parsed data from signature verification, or fall back to request.data
        if data is None:
            data = request.data

        # ZeptoMail webhook structure:
        # - event_name: array like ["hardbounce"]
        # - event_message: array of message objects
        event_names = data.get("event_name", [])
        event_messages = data.get("event_message", [])

        # Only process hard bounces
        if "hardbounce" not in event_names:
            return Response(
                {"status": "ok", "message": "No hard bounces"},
                status=status.HTTP_200_OK,
            )

        bounced_emails = set()

        for message in event_messages:
            event_data_list = message.get("event_data", [])

            for event_data in event_data_list:
                if event_data.get("object") != "hardbounce":
                    continue

                details = event_data.get("details", [])
                for detail in details:
                    bounced_recipient = detail.get("bounced_recipient")
                    if bounced_recipient:
                        bounced_emails.add(bounced_recipient.lower())

        # Mark emails as invalid
        for email in bounced_emails:
            try:
                user = User.objects.get(email__iexact=email)
                user.is_email_valid = False
                user.save(update_fields=["is_email_valid"])
                logger.info(f"Marked email as invalid due to hard bounce: {email}")
            except User.DoesNotExist:
                logger.debug(f"Bounced email not found in users: {email}")

        return Response(
            {"status": "ok", "message": "Bounced emails marked as invalid"},
            status=status.HTTP_200_OK,
        )
