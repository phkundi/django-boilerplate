from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.utils import timezone
import logging

from .serializers import TrackingEventSerializer
from .services.tracking_service import TrackingService, TrackingEvent
from .events import ALL_EVENT_DEFINITIONS

logger = logging.getLogger(__name__)


class TrackEventView(APIView):
    """
    Generic endpoint to receive tracking events from frontend
    Accepts both authenticated and anonymous requests
    """

    permission_classes = [AllowAny]
    serializer_class = TrackingEventSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)

        if not serializer.is_valid():
            return Response(
                {"error": "Invalid event data", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Get the event definition
            event_name = serializer.validated_data["event"]
            event_definition = ALL_EVENT_DEFINITIONS.get(event_name)

            # Create tracking event
            tracking_event = TrackingEvent(
                event=event_definition,
                label=serializer.validated_data.get("label"),
                value=serializer.validated_data.get("value"),
                user_id=str(request.user.id) if request.user.is_authenticated else None,
                session_id=serializer.validated_data.get("session_id"),
                properties=serializer.validated_data.get("properties", {}),
            )

            # Add request metadata to properties
            tracking_event.properties.update(
                {
                    "ip_address": self._get_client_ip(request),
                    "user_agent": request.META.get("HTTP_USER_AGENT", ""),
                    "timestamp": timezone.now().isoformat(),
                    "authenticated": request.user.is_authenticated,
                }
            )

            # Track the event
            tracking_service = TrackingService()
            tracking_service.track_event(tracking_event)

            return Response(
                {
                    "success": True,
                    "message": f"Event '{event_name}' tracked successfully",
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            logger.error(f"Error tracking event in endpoint: {str(e)}")
            # dont throw error to the frontend, just log it
            return Response(
                {"error": "Failed to track event", "message": str(e)},
                status=status.HTTP_200_OK,
            )

    def _get_client_ip(self, request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip


class AliasUserView(APIView):
    """
    Endpoint to alias a user's previous anonymous session with their authenticated user ID
    This links the anonymous events with the authenticated user in PostHog
    """

    permission_classes = [AllowAny]

    def post(self, request):
        try:
            session_id = request.data.get("session_id")
            user_id = request.data.get("user_id")

            if not session_id or not user_id:
                return Response(
                    {"error": "Both session_id and user_id are required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Call the tracking service to alias the user
            tracking_service = TrackingService()
            tracking_service.alias_user(
                user_id=str(user_id), previous_session_id=session_id
            )

            return Response(
                {
                    "success": True,
                    "message": "User aliased successfully",
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(f"Error aliasing user: {str(e)}")
            return Response(
                {"error": "Failed to alias user", "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
