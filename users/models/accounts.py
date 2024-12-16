from django.db import models
from core.models import BaseModel
from core.models import BaseModel
from django.db import models
from django.conf import settings
from django.utils.crypto import get_random_string


class Account(BaseModel):
    name = models.CharField(max_length=255)
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        verbose_name = "Account"
        verbose_name_plural = "Accounts"

    def __str__(self):
        return self.name


def generate_token():
    return get_random_string(64)


class AccountInvite(BaseModel):
    email = models.EmailField()
    inviter = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, related_name="sent_invites"
    )
    company = models.ForeignKey(
        "users.Company", on_delete=models.CASCADE, related_name="team_invites"
    )
    token = models.CharField(max_length=255, default=generate_token)

    def get_accept_url(self):
        return f"{settings.APP_URL}/register?inviteToken={self.token}&company={self.company.name}&email={self.email}&inviter={self.inviter.first_name}"
