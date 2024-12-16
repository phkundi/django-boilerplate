from django.urls import path, include
from .api import *
from rest_framework import routers


user_router = routers.DefaultRouter()
user_router.register("accounts", AccountViewSet, basename="accounts")

urlpatterns = [
    path("token/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", CustomTokenRefreshView.as_view(), name="token_refresh"),
    path("register/", RegisterView.as_view(), name="register"),
    path("forgot-password/", ForgotPasswordView.as_view(), name="forgot-password"),
    path(
        "reset-password/<user_id>/<token>/",
        ResetPasswordView.as_view(),
        name="reset-password",
    ),
    path("me/", GetAuthenticatedUser.as_view(), name="me"),
    path("stats/", UserStats.as_view(), name="stats"),
    path("delete-user/", DeleteUserView.as_view(), name="delete-user"),
    path("verify-email/", VerifyEmailView.as_view(), name="verify-email"),
    path("", include(user_router.urls)),
]
