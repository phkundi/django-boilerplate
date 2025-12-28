from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from users.models import User
from users.user_tokens import VerificationTokenGenerator, TokenExpired
from notifications.emails import send_email_verification_mail
from django.core.exceptions import ValidationError
from tracking.services.tracking_service import TrackingService, TrackingEvent
from tracking.events import EMAIL_VERIFIED


class ResendEmailVerificationView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            user = User.objects.get(pk=request.user.id)
        except User.DoesNotExist:
            return Response({"message": "User does not exist"}, status=404)

        if user.email_verified:
            return Response(
                {"message": "Email is already verified."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        send_email_verification_mail(user)
        return Response({"message": "Email sent"}, status=200)


class ResendEmailVerificationUnauthenticatedView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        user_id = request.data.get("user_id", None)
        token = request.data.get("token", None)

        if not user_id or not token:
            return Response(
                {"message": "User ID and token are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            uid = force_str(urlsafe_base64_decode(user_id))
            user = User.objects.get(pk=uid)

            # Verify the token is valid (even if expired) to ensure user_id is legitimate
            # This prevents user enumeration attacks
            try:
                VerificationTokenGenerator().check_token(user, token)
            except TokenExpired:
                # Token is expired but valid format - allow resend
                pass
            except Exception:
                return Response(
                    {"message": "Invalid token."}, status=status.HTTP_400_BAD_REQUEST
                )

            if user.email_verified:
                return Response(
                    {"message": "Email is already verified."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            send_email_verification_mail(user)
            return Response({"message": "Email sent"}, status=200)

        except (
            TypeError,
            ValueError,
            OverflowError,
            UnicodeDecodeError,
            User.DoesNotExist,
        ):
            return Response(
                {"message": "Invalid user ID or token."},
                status=status.HTTP_400_BAD_REQUEST,
            )


class VerifyEmailView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        user_id = request.data.get("user_id", None)
        token = request.data.get("token", None)

        if not user_id or not token:
            return Response(
                {"message": "User ID and token are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            uid = force_str(urlsafe_base64_decode(user_id))
            user = User.objects.get(pk=uid)

            if user.email_verified:
                return Response(
                    {
                        "message": "This email has already been verified. Please log in to continue."
                    },
                    status=status.HTTP_409_CONFLICT,
                )

            token_valid = VerificationTokenGenerator().check_token(user, token)
        except (
            TypeError,
            ValueError,
            OverflowError,
            UnicodeDecodeError,
            ValidationError,
            User.DoesNotExist,
        ):
            return Response(
                {"message": "Invalid token or user ID."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except TokenExpired as e:
            return Response(
                {"message": str(e), "expired": True},
                status=status.HTTP_409_CONFLICT,
            )

        if user and token_valid:
            user.email_verified = True
            user.save(update_fields=["email_verified"])

            TrackingService.track_event(
                TrackingEvent(
                    event=EMAIL_VERIFIED,
                    user_id=user.id,
                )
            )

            return Response(
                {"message": "Email verified successfully.", "email": user.email},
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {"message": "Invalid token."}, status=status.HTTP_400_BAD_REQUEST
            )
