# helper functions to add users to mailing list from sender.net

import requests
from django.conf import settings

base_url = "https://api.sender.net/v2/"

group_ids = {"signups": "aQ506M", "other": "dR5oPz"}


def get_headers():
    return {
        "Authorization": f"Bearer {settings.SENDER_API_TOKEN}",
        "Accept": "application/json",
    }


def add_to_mailing_list(email, group="signups"):
    if settings.DEBUG or settings.ENVIRONMENT != "production":
        return

    url = f"{base_url}subscribers/"
    headers = get_headers()

    try:
        response = requests.post(
            url,
            headers=headers,
            json={"email": email, "groups": [group_ids[group]]},
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return {"error": str(e)}


def update_subscriber(email, data):
    if settings.DEBUG or settings.ENVIRONMENT != "production":
        return

    if not email:
        raise ValueError("Email is required")

    url = f"{base_url}subscribers/{email}"
    headers = get_headers()

    try:
        response = requests.patch(
            url,
            headers=headers,
            json=data,
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return {"error": str(e)}
