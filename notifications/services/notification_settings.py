DEFAULT_CHOICES = [
    {
        "label": "Email",
        "value": "EMAIL",
    },
    {
        "label": "Push",
        "value": "PUSH",
    },
    {
        "label": "All",
        "value": "ALL",
    },
    {
        "label": "None",
        "value": "NONE",
    },
]

PUSH_ONLY_CHOICES = [
    {
        "label": "Push",
        "value": "PUSH",
    },
    {
        "label": "None",
        "value": "NONE",
    },
]


def get_user_notification_settings(user):
    """
    Get the user's notification settings

    Example:
      {
        "label": "New Follower",
        "description": "Notify me when I get a new follower",
        "value": user.notification_settings.new_follower,
        "field": "new_follower",
        "choices": DEFAULT_CHOICES
    }
    """
    return []
