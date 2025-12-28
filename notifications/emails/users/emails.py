from django.conf import settings
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from urllib.parse import quote
from notifications.services.email_service import EmailService
from notifications.constants.notification_types import (
    WELCOME_MAIL,
    PASSWORD_RESET,
    EMAIL_VERIFICATION,
)
from users.user_tokens import VerificationTokenGenerator


def send_welcome_mail(data):
    email = data.get("email", None)

    if not email:
        raise ValueError("No email found")

    email_type = WELCOME_MAIL

    EmailService.send_email(
        subject="Welcome to FLYP Fantasy",
        template_name="welcome-mail.html",
        context={
            "email_type": email_type,
            "email": quote(email),
        },
        recipients=[email],
        tracking={
            "email_type": email_type,
        },
    )


def send_password_reset_mail(data):
    user = data.get("user", None)
    if not user:
        raise ValueError("No user found")

    token_generator = PasswordResetTokenGenerator()
    token = token_generator.make_token(user)
    user_id = urlsafe_base64_encode(force_bytes(user.pk))

    email_type = PASSWORD_RESET

    EmailService.send_email(
        subject="Reset your FLYP Fantasy password",
        template_name="password-reset.html",
        context={
            "reset_url": f"{settings.APP_URL}/reset-password?user_id={user_id}&token={token}&email_click={email_type}",
            "email_type": email_type,
            "email": quote(user.email),
        },
        recipients=[user.email],
        tracking={
            "email_type": email_type,
            "reference_id": user.id,
        },
    )


def send_email_verification_mail(user):
    token_generator = VerificationTokenGenerator()
    verification_token = token_generator.make_token(user)
    user_id = urlsafe_base64_encode(force_bytes(user.pk))

    email_type = EMAIL_VERIFICATION

    verification_url = (
        f"{settings.APP_URL}/verify-email?user_id={user_id}&token={verification_token}"
    )

    EmailService.send_email(
        subject="Verify your email address",
        template_name="email-verification.html",
        context={
            "verification_url": verification_url,
            "email_type": email_type,
            "email": quote(user.email),
        },
        recipients=[user.email],
        tracking={
            "email_type": email_type,
        },
    )
