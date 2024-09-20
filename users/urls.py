from django.urls import path, include
from .api import (
    RegisterView,
    GetAuthenticatedUser,
    ForgotPasswordView,
    ResetPasswordView,
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    UserStats,
    DeleteAccountView,
)
from rest_framework import routers


user_router = routers.DefaultRouter()

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
    path("delete-account/", DeleteAccountView.as_view(), name="delete-account"),
    path("", include(user_router.urls)),
]
