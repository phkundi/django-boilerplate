from core.models import BaseModel
from django.db import models


class AccountUser(BaseModel):

    ROLES = [
        ("ADMIN", "Admin"),
        ("USER", "User"),
    ]

    account = models.ForeignKey(
        "users.Account", on_delete=models.CASCADE, related_name="account_users"
    )
    user = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, related_name="account_users"
    )
    role = models.CharField(max_length=255, choices=ROLES)

    class Meta:
        verbose_name = "Account User"
        verbose_name_plural = "Account Users"

    def __str__(self):
        return f"{self.user.email} - {self.account.name}"
