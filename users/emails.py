import threading
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from core.emails import email_sender
from django.conf import settings
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode


def send_welcome_mail(recipient_email):
    url = f"{settings.APP_URL}/login"
    html_content = render_to_string("welcome-mail.html", {"url": url})
    text_content = strip_tags(html_content)
    thread = threading.Thread(
        target=email_sender,
        args=(
            f"Welcome to {settings.APP_NAME}",
            text_content,
            html_content,
            [recipient_email],
        ),
    )
    thread.start()


def send_password_reset_mail(user):
    token_generator = PasswordResetTokenGenerator()
    token = token_generator.make_token(user)
    user_id = urlsafe_base64_encode(force_bytes(user.pk))

    subject = "Reset your FYLP Password"
    reset_url = f"{settings.LANDING_URL}/reset-password?user_id={user_id}&token={token}"
    print(reset_url)
    html_content = render_to_string(
        "password-reset.html",
        {"reset_url": reset_url},
    )
    text_content = strip_tags(html_content)
    thread = threading.Thread(
        target=email_sender, args=(subject, text_content, html_content, [user.email])
    )
    thread.start()


def send_connection_request_mail(connection_request):
    target_url = f"{settings.APP_URL}/user/notifications"

    html_content = render_to_string(
        "connection-request.html",
        {
            "target_url": target_url,
            "requester_username": connection_request.user.username,
        },
    )
    text_content = strip_tags(html_content)
    thread = threading.Thread(
        target=email_sender,
        args=(
            "New Connection Request",
            text_content,
            html_content,
            [connection_request.connection.email],
        ),
    )
    thread.start()


def send_invite_mail(inviter, email, source, league_id):
    target_url = (
        f"{settings.LANDING_URL}/register?"
        f"inviterId={inviter.id}&"
        f"inviteEmail={email}&"
        f"inviterUsername={inviter.username}&"
        f"utm_source={source}&"
        "utm_medium=email_invite&"
        f"utm_content={inviter.username}"
    )

    if league_id:
        target_url += f"&leagueId={league_id}"

    html_content = render_to_string(
        "user-invite.html",
        {
            "target_url": target_url,
            "inviter": inviter.username,
        },
    )

    text_content = strip_tags(html_content)
    thread = threading.Thread(
        target=email_sender,
        args=(
            f"You have been invited to {settings.APP_NAME}",
            text_content,
            html_content,
            [email],
        ),
    )
    thread.start()
