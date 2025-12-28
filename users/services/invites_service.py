from tracking.services.tracking_service import TrackingService, TrackingEvent
from tracking.events import ACCEPT_INVITE, USER_REFERRED


class InvitesService:

    @staticmethod
    def handle_invite_accepted(new_user, inviter_id):
        from users.models import User

        try:
            inviter = User.objects.get(id=inviter_id)
        except User.DoesNotExist:
            return None

        new_user.referred_by = inviter
        new_user.save()

        TrackingService.track_event(
            TrackingEvent(
                event=ACCEPT_INVITE,
                user_id=new_user.id,
            )
        )
        TrackingService.track_event(
            TrackingEvent(
                event=USER_REFERRED,
                user_id=inviter.id,
                properties={
                    "referrer_email": inviter.email,
                },
            )
        )
