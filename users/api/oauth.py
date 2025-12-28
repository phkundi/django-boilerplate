import re
import logging
import jwt
import time
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import update_last_login
from rest_framework import status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from google.oauth2 import id_token
from google.auth.transport import requests
from allauth.socialaccount.models import SocialAccount
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.apple.views import AppleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView
from tracking.services.tracking_service import TrackingService, TrackingEvent
from tracking.events import USER_LOGIN, USER_REGISTER
from users.serializers.users import UserBaseSerializer
from users.services import InvitesService

logger = logging.getLogger(__name__)


class GoogleOAuth2LoginView(SocialLoginView):
    """
    Simplified Google OAuth2 login view for both web and Capacitor clients
    Handles ID tokens from Google's JavaScript SDK
    """

    adapter_class = GoogleOAuth2Adapter
    callback_url = "postmessage"  # For web clients using Google's JS library
    client_class = OAuth2Client

    def post(self, request, *args, **kwargs):
        # Handle ID token from Google's JavaScript SDK
        id_token_str = request.data.get(
            "access_token"
        )  # Frontend sends as access_token

        if id_token_str:
            try:
                # Verify the ID token
                client_id = settings.GOOGLE_OAUTH2_CLIENT_ID

                if not client_id:

                    return Response(
                        {"error": "Google OAuth2 client ID not configured"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    )

                # Verify the token
                id_info = id_token.verify_oauth2_token(
                    id_token_str, requests.Request(), client_id
                )

                # Check if token is valid
                if id_info["iss"] not in [
                    "accounts.google.com",
                    "https://accounts.google.com",
                ]:
                    return Response(
                        {"error": "Invalid token issuer"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                # Handle user creation/authentication
                inviter_id = request.data.get("inviterId", None)

                source = request.data.get("source", None)
                return self._handle_google_auth(id_info, inviter_id, source)

            except ValueError as e:
                logger.error(f"ID token verification failed: {e}")
                return Response(
                    {"error": "Invalid ID token"}, status=status.HTTP_400_BAD_REQUEST
                )

        # Fallback to original dj-rest-auth flow
        response = super().post(request, *args, **kwargs)

        if response.status_code == 200 and hasattr(response, "data"):
            user = request.user
            if user and user.is_authenticated:
                # Track login event
                TrackingService.track_event(
                    TrackingEvent(
                        event=USER_LOGIN,
                        user_id=user.id,
                        properties={"provider": "google"},
                    )
                )
                update_last_login(None, user)

        return response

    def _handle_google_auth(self, id_info, inviter_id=None, source=None):
        """Handle Google authentication with ID token info"""
        try:

            # Extract user info from the token
            email = id_info.get("email")
            google_id = id_info.get("sub")
            first_name = id_info.get("given_name", "")
            last_name = id_info.get("family_name", "")

            if not email or not google_id:
                return Response(
                    {"error": "Unable to get user info from token"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            User = get_user_model()

            # Check if social account already exists
            try:
                social_account = SocialAccount.objects.get(
                    provider="google", uid=google_id
                )
                user = social_account.user
                is_new_user = False
            except SocialAccount.DoesNotExist:
                # Check if user with this email already exists
                try:
                    user = User.objects.get(email=email)
                    is_new_user = False

                    # Create social account for existing user
                    social_account = SocialAccount.objects.create(
                        user=user, provider="google", uid=google_id, extra_data=id_info
                    )
                except User.DoesNotExist:
                    # Create new user
                    is_new_user = True

                    # Generate unique username from email
                    # base_username = email.split("@")[0]

                    # base_username = re.sub(r"[^a-zA-Z0-9]", "", base_username)

                    # username = base_username.lower()
                    # counter = 1
                    # while User.objects.filter(username=username).exists():
                    #     username = f"{base_username}{counter}".lower()
                    #     counter += 1

                    # Create the user
                    user = User.objects.create(
                        email=email.lower(),
                        # username=username,
                        first_name=first_name,
                        last_name=last_name,
                        is_active=True,
                        email_verified=True,
                    )

                    # Create social account
                    social_account = SocialAccount.objects.create(
                        user=user, provider="google", uid=google_id, extra_data=id_info
                    )

            # Handle referral and league membership for new users only
            if is_new_user:
                if inviter_id:
                    InvitesService.handle_invite_accepted(user, inviter_id)

            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            # refresh["username"] = user.username
            refresh["is_staff"] = user.is_staff

            access_token = refresh.access_token
            # access_token["username"] = user.username
            access_token["is_staff"] = user.is_staff

            # Update last login
            update_last_login(None, user)

            # Track events
            if is_new_user:
                TrackingService.track_event(
                    TrackingEvent(
                        event=USER_REGISTER,
                        user_id=user.id,
                        properties={
                            "provider": "google",
                            "inviter_id": inviter_id,
                            "source": source,
                        },
                    )
                )

            TrackingService.track_event(
                TrackingEvent(
                    event=USER_LOGIN,
                    user_id=user.id,
                    properties={"provider": "google"},
                )
            )

            # Return user data with tokens
            user_data = UserBaseSerializer(user, context={"user": user}).data

            return Response(
                {
                    "access": str(access_token),
                    "refresh": str(refresh),
                    "user": user_data,
                    "is_new_user": is_new_user,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(f"Google auth error: {e}")
            return Response(
                {"error": "Authentication failed"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class AppleOAuth2LoginView(SocialLoginView):
    """
    Apple OAuth2 login view for both web and Capacitor clients
    Handles identity tokens from Apple's Sign-In service
    """

    adapter_class = AppleOAuth2Adapter
    client_class = OAuth2Client

    def post(self, request, *args, **kwargs):
        try:  # Handle identity token from Apple's Sign-In service
            identity_token = request.data.get("id_token") or request.data.get(
                "identity_token"
            )

            if identity_token:
                try:
                    # Verify and decode the Apple identity token
                    decoded_token = self._verify_apple_token(identity_token)

                    if decoded_token:
                        # Handle user creation/authentication
                        inviter_id = request.data.get("inviterId", None)
                        source = request.data.get("source", None)
                        return self._handle_apple_auth(
                            decoded_token, request.data, inviter_id, source
                        )
                    else:
                        return Response(
                            {"error": "Invalid Apple identity token"},
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                except Exception as e:
                    logger.error(f"Apple token verification failed: {e}")
                    return Response(
                        {"error": "Invalid Apple identity token"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            # Fallback to original dj-rest-auth flow
            response = super().post(request, *args, **kwargs)

            if response.status_code == 200 and hasattr(response, "data"):
                user = request.user
                if user and user.is_authenticated:
                    # Track login event
                    TrackingService.track_event(
                        TrackingEvent(
                            event=USER_LOGIN,
                            user_id=user.id,
                            properties={"provider": "apple"},
                        )
                    )
                    update_last_login(None, user)

            return response
        except Exception as e:
            logger.error(f"Apple auth error: {e}")
            return Response(
                {"error": "Authentication failed"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def _verify_apple_token(self, identity_token):
        """Verify Apple identity token"""
        try:
            # For development/testing, we'll decode without verification
            # In production, you should verify against Apple's public keys
            decoded = jwt.decode(identity_token, options={"verify_signature": False})

            # Basic validation
            if decoded.get("iss") != "https://appleid.apple.com":
                return None

            # Check audience against all valid client IDs
            token_audience = decoded.get("aud")
            if token_audience not in settings.APPLE_VALID_CLIENT_IDS:
                logger.warning(f"Invalid Apple token audience: {token_audience}")
                return None

            # Check expiration
            if decoded.get("exp", 0) < time.time():
                return None

            return decoded

        except jwt.InvalidTokenError:
            return None

    def _handle_apple_auth(
        self, token_data, request_data, inviter_id=None, source=None
    ):
        """Handle Apple authentication with token data"""
        try:
            # Extract user info from the token
            apple_id = token_data.get("sub")
            email = token_data.get("email")

            # Apple may not always provide email in the token
            # It's usually provided in the user object on first sign-in
            user_info = request_data.get("user")
            if user_info and isinstance(user_info, dict):
                if not email:
                    email = user_info.get("email")
                first_name = user_info.get("name", {}).get("firstName", "")
                last_name = user_info.get("name", {}).get("lastName", "")
            else:
                first_name = ""
                last_name = ""

            if not apple_id:
                return Response(
                    {"error": "Unable to get Apple ID from token"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            User = get_user_model()

            # Check if social account already exists
            try:
                social_account = SocialAccount.objects.get(
                    provider="apple", uid=apple_id
                )
                user = social_account.user
                is_new_user = False
            except SocialAccount.DoesNotExist:
                # Check if user with this email already exists (if email is available)
                if email:
                    try:
                        user = User.objects.get(email=email)
                        is_new_user = False

                        # Create social account for existing user
                        social_account = SocialAccount.objects.create(
                            user=user,
                            provider="apple",
                            uid=apple_id,
                            extra_data=token_data,
                        )
                    except User.DoesNotExist:
                        # Create new user
                        is_new_user = True
                        user = self._create_apple_user(
                            email, first_name, last_name, apple_id, token_data
                        )
                else:
                    # No email provided, create user with Apple ID
                    is_new_user = True
                    user = self._create_apple_user(
                        None, first_name, last_name, apple_id, token_data
                    )

            # Handle referral and league membership for new users only
            if is_new_user:
                if inviter_id:
                    InvitesService.handle_invite_accepted(user, inviter_id)

            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            # refresh["username"] = user.username
            refresh["is_staff"] = user.is_staff

            access_token = refresh.access_token
            # access_token["username"] = user.username
            access_token["is_staff"] = user.is_staff

            # Update last login
            update_last_login(None, user)

            # Track events
            if is_new_user:
                TrackingService.track_event(
                    TrackingEvent(
                        event=USER_REGISTER,
                        user_id=user.id,
                        properties={
                            "provider": "apple",
                            "inviter_id": inviter_id,
                            "source": source,
                        },
                    )
                )

            TrackingService.track_event(
                TrackingEvent(
                    event=USER_LOGIN,
                    user_id=user.id,
                    properties={"provider": "apple"},
                )
            )

            # Return user data with tokens
            user_data = UserBaseSerializer(user, context={"user": user}).data

            return Response(
                {
                    "access": str(access_token),
                    "refresh": str(refresh),
                    "user": user_data,
                    "is_new_user": is_new_user,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(f"Apple auth error: {e}")
            return Response(
                {"error": "Authentication failed"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def _create_apple_user(self, email, first_name, last_name, apple_id, token_data):
        """Create a new user for Apple Sign-In"""
        User = get_user_model()

        # Generate username
        # if email:
        #     base_username = email.split("@")[0]
        #     base_username = re.sub(r"[^a-zA-Z0-9]", "", base_username)
        # else:
        #     base_username = f"apple_user_{apple_id[:8]}"

        # username = base_username.lower()
        # counter = 1
        # while User.objects.filter(username=username).exists():
        #     username = f"{base_username}{counter}".lower()
        #     counter += 1

        # Create the user
        user = User.objects.create(
            email=email.lower() if email else "",
            # username=username,
            first_name=first_name,
            last_name=last_name,
            is_active=True,
            email_verified=True,
        )

        # Create social account
        SocialAccount.objects.create(
            user=user, provider="apple", uid=apple_id, extra_data=token_data
        )

        return user
