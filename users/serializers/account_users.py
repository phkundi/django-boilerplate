from rest_framework import serializers
from users.models import AccountUser
from users.serializers.users import UserSerializer


class AccountUserSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = AccountUser
        fields = ["id", "user", "role"]
