from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import get_user_model

from users.serializers import (
    RegisterSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer,
    UserSerializer,
)
from users.emails import send_welcome_mail, send_password_reset_mail
from users.services import add_to_mailing_list

from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth import authenticate
from rest_framework_simplejwt.views import TokenRefreshView, TokenObtainPairView
from users.serializers.auth import (
    RegisterSerializer,
    CustomTokenObtainPairSerializer,
    CustomTokenRefreshSerializer,
)


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class CustomTokenRefreshView(TokenRefreshView):
    serializer_class = CustomTokenRefreshSerializer


class GetAuthenticatedUser(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = request.user
        return Response(UserSerializer(user).data, status=200)


class RegisterView(generics.CreateAPIView):
    User = get_user_model()
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        credentials = request.data.get("credentials", {})

        serializer = self.get_serializer(data=credentials)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        headers = self.get_success_headers(serializer.data)

        user_data = UserSerializer(user).data
        send_welcome_mail(user.email)
        add_to_mailing_list(user.email)

        return Response(user_data, status=status.HTTP_201_CREATED, headers=headers)


class ForgotPasswordView(APIView):
    serializer_class = ForgotPasswordSerializer
    permission_classes = (AllowAny,)

    def post(self, request):
        User = get_user_model()

        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data["email"]
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response(
                    {"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND
                )

            send_password_reset_mail(user)

            return Response(
                {"detail": "Password reset link sent"}, status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResetPasswordView(APIView):
    serializer_class = ResetPasswordSerializer
    permission_classes = (AllowAny,)

    def post(self, request, user_id, token):
        User = get_user_model()

        try:
            uid = force_str(urlsafe_base64_decode(user_id))
            user = User.objects.get(pk=uid)

            if PasswordResetTokenGenerator().check_token(user, token):
                serializer = self.serializer_class(data=request.data)
                serializer.is_valid(raise_exception=True)
                # Set new password
                password = request.data.get("password1")
                user.set_password(password)
                user.save()
                return Response(
                    {"detail": "Password reset successful", "email": user.email},
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {"detail": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST
                )
        except (TypeError, ValueError, OverflowError, User.DoesNotExist) as e:
            return Response(
                {"detail": "Invalid user"}, status=status.HTTP_400_BAD_REQUEST
            )


class ChangePasswordView(APIView):
    def post(self, request, *args, **kwargs):
        current_password = request.data.get("currentPassword")
        new_password = request.data.get("newPassword1")
        confirm_new_password = request.data.get("newPassword2")

        if not current_password or not new_password or not confirm_new_password:
            return Response({"message": "Please fill all fields"}, status=400)

        if new_password != confirm_new_password:
            return Response({"message": "New passwords must match."}, status=400)

        if len(new_password) < 8:
            return Response(
                {"message": "Password must have at least 8 characters"}, status=400
            )

        user = authenticate(email=request.user.email, password=current_password)

        if user is None:
            return Response({"message": "Current password is incorrect."}, status=400)

        user.set_password(new_password)
        user.save()

        return Response({"success": "Password updated successfully"}, status=200)
