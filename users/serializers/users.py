from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken


class UserBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ["id", "first_name", "last_name", "username", "country", "created_at"]


class UserSerializer(UserBaseSerializer):
    class Meta(UserBaseSerializer.Meta):
        fields = UserBaseSerializer.Meta.fields + ["email", "birthday", "is_staff"]


class AccountUpdateSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=30, required=True)
    last_name = serializers.CharField(
        max_length=50, required=False, allow_null=True, allow_blank=True
    )
    birthday = serializers.DateField(required=False, allow_null=True)
    country = serializers.CharField(
        max_length=50, required=False, allow_null=True, allow_blank=True
    )

    def validate(self, data):
        """
        Validate the input data and raise errors if something went wrong
        """

        return data

    def check_necessary_fields(self, user, data):
        """
        This function is to make sure that the user doesn't remove necessary information. Raise error if yes
        """
        pass

    def update(self, instance, validated_data):
        """
        Update the user and creator models with the validated data.
        """
        user = instance

        user.first_name = validated_data.get("first_name", user.first_name)
        user.last_name = validated_data.get("last_name", user.last_name)
        user.birthday = validated_data.get("birthday", user.birthday)
        user.country = validated_data.get("country", user.country)

        user.save()

        return user

    def get_token(self, user):
        """
        Generate a new token with the updated user data.
        """
        refresh = RefreshToken.for_user(user)
        # Add extra info
        refresh.payload["email"] = user.email
        refresh.payload["firstName"] = user.first_name
        refresh.payload["lastName"] = user.last_name
        refresh.payload["username"] = user.username

        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }
