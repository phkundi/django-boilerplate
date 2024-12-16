import logging
import stripe
from django.conf import settings
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from users.models import Account, AccountInvite, AccountUser
from users.serializers import (
    AccountSerializer,
    AccountInviteSerializer,
    AccountUserSerializer,
)


logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY


class AccountViewSet(viewsets.ModelViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer

    def retrieve(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        account = request.user.current_account
        serializer = self.get_serializer(account)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        account = serializer.save()

        request.user.current_account = account
        request.user.save()

        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    @action(detail=True, methods=["get"], url_path="team-members")
    def get_team_members(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        account = self.get_object()
        members = account.account_users.all().select_related("user")
        invites = account.account_invites.all()
        user_serializer = AccountUserSerializer(members, many=True)
        invite_serializer = AccountInviteSerializer(invites, many=True)
        return Response(
            {"users": user_serializer.data, "invites": invite_serializer.data}
        )

    @action(detail=True, methods=["delete"], url_path="remove-team-member/<user_id>")
    def remove_team_member(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.current_account:
            return Response(
                {"message": "You must be logged in to remove a team member"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        account = self.get_object()
        if request.user.current_account != account:
            return Response(
                {"message": "You can only remove team members from your own account"},
                status=status.HTTP_403_FORBIDDEN,
            )

        user_id = kwargs.get("user_id")

        account_user = AccountUser.objects.get(user_id=user_id, account=account)
        user = account_user.user
        user.current_account = None

        user.save()
        account_user.delete()

        return Response({"message": "Team member removed"}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="invite-team")
    def invite_team(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        account = self.get_object()
        if request.user.current_account != account:
            return Response(
                {"message": "You can only invite team members to your own account"},
                status=status.HTTP_403_FORBIDDEN,
            )

        emails = request.data.get("emails", [])
        for email in emails:
            invite, _ = AccountInvite.objects.get_or_create(
                email=email, account=account, inviter=request.user
            )
            # TODO: send invite email

        return Response({"message": "Invites sent"}, status=status.HTTP_200_OK)

    def partial_update(self, request, *args, **kwargs):
        try:
            if not request.user.is_authenticated:
                return Response(status=status.HTTP_401_UNAUTHORIZED)

            account = self.get_object()
            if request.user.current_account != account:
                return Response(
                    {"message": "You can only update your own account"},
                    status=status.HTTP_403_FORBIDDEN,
                )

            serializer = AccountSerializer(account, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()

            return Response(serializer.data)
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"], url_path="signup-completed")
    def signup_completed(self, request, *args, **kwargs):
        account = self.get_object()
        # TODO: send welcome email to account

        return Response({"success": True}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="accept-invite")
    def accept_invite(self, request, *args, **kwargs):
        invite_token = request.data.get("inviteToken")
        invite = AccountInvite.objects.get(token=invite_token)

        if invite.email != request.user.email:
            return Response(
                {"message": "You cannot accept this invite"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        AccountUser.objects.create(
            user=request.user,
            account=invite.account,
            role=AccountUser.Role.MEMBER,
        )
        request.user.current_account = invite.account
        request.user.save()

        invite.delete()

        return Response({"success": True}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="create-stripe-portal")
    def create_stripe_portal(self, request, *args, **kwargs):
        try:
            account = request.user.current_account
            if not account.stripe_customer_id:
                return Response(
                    {"error": "No Stripe customer found for this company"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            portal_session = stripe.billing_portal.Session.create(
                customer=account.stripe_customer_id,
                return_url=settings.APP_URL + "/settings",
            )

            return Response({"portal_url": portal_session.url})

        except Exception as e:
            logger.error("Failed to create portal session: %s", str(e), exc_info=True)
            return Response(
                {"error": "Failed to create portal session"},
                status=status.HTTP_400_BAD_REQUEST,
            )
