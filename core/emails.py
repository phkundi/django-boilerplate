import requests
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import threading


def email_sender(subject, text_content, html_content, recipients):

    from_email = settings.ZEPTOMAIL_FROM_EMAIL
    request_url = "https://api.zeptomail.eu/v1.1/email"

    headers = {
        "Authorization": settings.ZEPTOMAIL_TOKEN,
        "Content-Type": "application/json",
    }

    payload = {
        # "bounce_address": from_email,
        "from": {"address": from_email, "name": settings.APP_NAME},
        "to": [{"email_address": {"address": recipient}} for recipient in recipients],
        "subject": subject,
        "htmlbody": html_content,
        "textbody": text_content,
    }

    response = requests.post(request_url, headers=headers, json=payload)

    if response.status_code >= 400:
        raise Exception(f"Failed to send email: {response.status_code} {response.text}")
    else:
        print(f"Email sent successfully: {response.status_code}")


def send_contact_notification(data):

    subject = f"New Contact Form Submission from {data['name']}"

    html_content = render_to_string(
        "contact-form-notification.html",
        {
            "name": data["name"],
            "company": data["company"] if "company" in data else None,
            "email": data["email"],
            "message": data["message"],
        },
    )
    text_content = strip_tags(html_content)
    thread = threading.Thread(
        target=email_sender,
        args=(
            subject,
            text_content,
            html_content,
            [settings.ADMIN_EMAIL],
        ),
    )
    thread.start()
