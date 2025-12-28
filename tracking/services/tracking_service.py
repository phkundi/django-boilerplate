from dataclasses import dataclass
from typing import Optional, Dict, Any
import logging
import posthog


logger = logging.getLogger(__name__)


@dataclass
class TrackingEvent:
    event: Any  # EventDefinition
    label: Optional[str] = None
    value: Optional[int] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None


class TrackingService:
    @staticmethod
    def track_event(event: TrackingEvent):
        """
        Track an event - store locally and send to integrations
        """
        try:
            logger.info(f"Tracking event: {event}")

            # Send to PostHog with enhanced tracking
            TrackingService._send_to_posthog(event)

        except Exception as e:
            logger.error(f"Failed to track event: {str(e)}")
            raise

    @staticmethod
    def alias_user(user_id: str, previous_session_id: str):
        """
        Link a user's previous anonymous session ID with their authenticated user ID
        This tells PostHog that these two identities belong to the same person

        Args:
            user_id: The authenticated user's ID (new distinct_id)
            previous_session_id: The anonymous session ID (old distinct_id)
        """
        try:
            if not previous_session_id or not user_id:
                logger.warning(
                    f"Cannot alias user - missing user_id ({user_id}) or session_id ({previous_session_id})"
                )
                return

            if previous_session_id == user_id:
                logger.debug("Session ID matches user ID, skipping alias")
                return

            logger.info(
                f"Aliasing user: linking session {previous_session_id} to user {user_id}"
            )
            posthog.alias(previous_id=previous_session_id, distinct_id=user_id)

        except Exception as e:
            logger.error(f"Failed to alias user in PostHog: {str(e)}")
            # Don't re-raise - aliasing failures shouldn't break the application

    @staticmethod
    def _send_to_posthog(event: TrackingEvent):
        """
        Send tracking event to PostHog with proper user identification and properties
        """
        try:
            # Prepare properties dictionary
            properties = event.properties.copy() if event.properties else {}

            # Add event metadata to properties
            if hasattr(event.event, "category"):
                properties["event_category"] = event.event.category

            if event.label:
                properties["event_label"] = event.label

            if event.value is not None:
                properties["event_value"] = event.value

            if event.session_id:
                properties["session_id"] = event.session_id

            if event.user_id:
                from users.models import User

                user = User.objects.get(id=event.user_id)
                name = f"{user.first_name if user.first_name else ''}{f" {user.last_name}" if user.last_name else ''}"
                properties["$set"] = {
                    # "username": user.username,
                    "email": user.email,
                    "name": name,
                    "country": user.country,
                    "last_seen": user.last_seen,
                    "email_verified": user.email_verified,
                    "attribution": user.attribution,
                }
                properties["$set_once"] = {
                    "date_joined": user.created_at,
                    "is_referred": user.referred_by is not None,
                    "referrer_email": (
                        user.referred_by.email if user.referred_by else None
                    ),
                }
                if user.birthday:
                    properties["$set_once"]["birthday"] = user.birthday

            posthog.capture(
                distinct_id=(
                    event.user_id if event.user_id else event.session_id or "anonymous"
                ),
                event=event.event.name,
                properties=properties,
            )

        except Exception as e:
            logger.error(f"Failed to send event to PostHog: {str(e)}")
            # Don't re-raise - PostHog failures shouldn't break the application
