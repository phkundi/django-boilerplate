from rest_framework import serializers
from users.models import AccountInvite, Account
from users.serializers.account_users import AccountUserSerializer


class AccountSerializer(serializers.ModelSerializer):
    users = AccountUserSerializer(many=True, read_only=True)

    class Meta:
        model = Account
        fields = ["id", "name", "users"]


class AccountInviteSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountInvite
        fields = ["id", "email", "created_at"]
