import requests
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import threading
from typing import Union, List


def filter_recipients(recipients: List[str]) -> List[str]:
    """
    Filter email recipients based on environment settings.
    In development, only allows emails from DEV_NOTIFICATIONS and their variations.
    In production, allows all emails.

    Args:
        recipients: List of email addresses

    Returns:
        List of allowed email addresses
    """
    if settings.ENVIRONMENT == "production":
        return recipients

    final_recipients = []
    for email in recipients:
        # Check if email is directly in DEV_NOTIFICATIONS
        if email in settings.DEV_NOTIFICATIONS:
            final_recipients.append(email)
            continue

        # Check if this is a variation of a whitelisted email
        base_email = email.split("+")[0] + "@" + email.split("@")[1]
        if base_email in settings.DEV_NOTIFICATIONS:
            final_recipients.append(email)

    return final_recipients


def email_sender(
    subject, text_content, html_content, recipients, from_email="noreply"
):
    final_recipients = filter_recipients(recipients)
    if not final_recipients:
        return

    if from_email not in settings.EMAIL_SENDERS:
        from_email = "noreply"

    request_url = "https://api.zeptomail.eu/v1.1/email"

    headers = {
        "Authorization": settings.ZEPTOMAIL_TOKEN,
        "Content-Type": "application/json",
    }

    payload = {
        "from": {
            "address": settings.EMAIL_SENDERS[from_email]["address"],
            "name": settings.EMAIL_SENDERS[from_email]["name"],
        },
        "to": [
            {"email_address": {"address": recipient}} for recipient in final_recipients
        ],
        "subject": subject,
        "htmlbody": html_content,
        "textbody": text_content,
    }

    response = requests.post(request_url, headers=headers, json=payload)

    if response.status_code >= 400:
        raise Exception(f"Failed to send email: {response.status_code} {response.text}")
    else:
        print(f"Email sent successfully: {response.status_code}")

        


class EmailService:
    @staticmethod
    def send_email(
        subject: str,
        template_name: str,
        context: dict,
        recipients: Union[str, List[str]],
        from_email: str = "noreply",
    ):
        """
        Send an email using a template.

        Args:
            subject: Email subject
            template_path: Full path to template (e.g., 'users/emails/welcome.html')
            context: Template context dictionary
            recipients: Single email or list of email addresses
            sender_name: Optional custom sender name (defaults to settings.APP_NAME)
        """
        if isinstance(recipients, str):
            recipients = [recipients]

        html_content = render_to_string(template_name, context)
        text_content = strip_tags(html_content)

        thread = threading.Thread(
            target=email_sender,
            args=(
                subject,
                text_content,
                html_content,
                recipients,
                from_email,
            ),
        )
        thread.start()
