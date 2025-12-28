from django.utils import timezone
from django.db import transaction


class UserActivityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Update last_activity for authenticated users
        if request.user.is_authenticated:
            today = timezone.now().date()

            # Use atomic transaction to prevent race conditions
            with transaction.atomic():
                # Re-fetch user with lock to ensure we have the latest data
                from users.models import User

                user = User.objects.select_for_update().get(pk=request.user.pk)

                # Only update if last_seen is not from today
                if user.last_seen < today:
                    user.last_seen = today
                    user.save(update_fields=["last_seen"])

        return response
