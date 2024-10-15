from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework import status
from rest_framework.permissions import AllowAny
from users.models import User
from users.emails import (
    send_welcome_mail,
    send_verification_email,
)
from users.user_tokens import VerificationTokenGenerator, TokenExpired


class ResendVerificationMail(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, user_id):
        try:
            uid = force_str(urlsafe_base64_decode(user_id))
            user = User.objects.get(pk=uid)
        except User.DoesNotExist:
            return Response({"message": "User does not exist"}, status=404)

        send_verification_email(user)
        return Response("Email sent", status=200)


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
            if user.is_active:
                return Response(
                    {
                        "message": "This account has already been activated. Please log in to continue."
                    },
                    status=409,
                )

            token_valid = VerificationTokenGenerator().check_token(user, token)
        except (
            TypeError,
            ValueError,
            OverflowError,
            UnicodeDecodeError,
            User.DoesNotExist,
        ) as e:
            user = None
            return Response({"message": "Invalid Token"}, status=400)
        except TokenExpired as e:
            return Response({"message": str(e)}, status=409)

        if user and token_valid:
            user.is_active = True
            user.save()
            # send_welcome_mail(user)

            return Response(
                {"message": "User activated successfully."}, status=status.HTTP_200_OK
            )
        else:
            return Response(
                {"message": "Invalid token."}, status=status.HTTP_400_BAD_REQUEST
            )
