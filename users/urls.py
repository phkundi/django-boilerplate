from django.urls import path, include
from .api import *
from rest_framework import routers


user_router = routers.DefaultRouter()
user_router.register("accounts", AccountViewSet, basename="accounts")

auth_routes = [
    path("token/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", CustomTokenRefreshView.as_view(), name="token_refresh"),
    path("register/", RegisterView.as_view(), name="register"),
    path("forgot-password/", ForgotPasswordView.as_view(), name="forgot-password"),
    path(
        "reset-password/<user_id>/<token>/",
        ResetPasswordView.as_view(),
        name="reset-password",
    ),
    # OAuth routes - single endpoint for both web and Capacitor
    path("auth/google/", GoogleOAuth2LoginView.as_view(), name="google_oauth2_login"),
    path("auth/apple/", AppleOAuth2LoginView.as_view(), name="apple_oauth2_login"),
]

email_verification_routes = [
    path(
        "email-verification/resend/",
        ResendEmailVerificationView.as_view(),
        name="resend-email-verification",
    ),
    path(
        "email-verification/resend-unauthenticated/",
        ResendEmailVerificationUnauthenticatedView.as_view(),
        name="resend-email-verification-unauthenticated",
    ),
    path("email-verification/verify/", VerifyEmailView.as_view(), name="verify-email"),
]

other_routes = [
    path("me/", GetAuthenticatedUser.as_view(), name="me"),
    path("delete-user/", DeleteUserView.as_view(), name="delete-user"),
    path("", include(user_router.urls)),
]

urlpatterns = auth_routes + email_verification_routes + other_routes
