from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from users.models import User
from django.db.models import Count


class UserStats(APIView):
    def get(self, request):
        if not request.user.is_staff:
            return Response(
                {"error": "You do not have permission to access this resource."},
                status=status.HTTP_403_FORBIDDEN,
            )

        user_count = User.objects.count()
        user_signups_7_days = User.objects.filter(
            date_joined__gte=timezone.now() - timezone.timedelta(days=7)
        ).count()
        user_signups_30_days = User.objects.filter(
            date_joined__gte=timezone.now() - timezone.timedelta(days=30)
        ).count()
        users_by_country = (
            User.objects.values("country")
            .annotate(count=Count("country"))
            .order_by("-count")
        )

        return Response(
            {
                "user_count": {
                    "total": user_count,
                    "7_days": user_signups_7_days,
                    "30_days": user_signups_30_days,
                },
                "by_country": users_by_country,
            },
            status=status.HTTP_200_OK,
        )
