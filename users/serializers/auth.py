from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from django.core.validators import RegexValidator
from django.contrib.auth.password_validation import validate_password
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
    TokenRefreshSerializer,
)
from rest_framework_simplejwt.tokens import RefreshToken


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        token["username"] = user.username

        return token


class CustomTokenRefreshSerializer(TokenRefreshSerializer):

    def validate(self, attrs):
        data = super().validate(attrs)

        refresh = RefreshToken(attrs["refresh"])
        access_token = refresh.access_token

        # Get the user_id from the refresh token
        User = get_user_model()
        user_id = refresh["user_id"]
        user = User.objects.get(id=user_id)

        # Add custom claims
        access_token["username"] = user.username

        data["access"] = str(access_token)

        return data


class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=get_user_model().objects.all())],
    )
    username = serializers.CharField(
        required=True,
        validators=[
            UniqueValidator(queryset=get_user_model().objects.all()),
            RegexValidator(
                regex="^[a-zA-Z0-9]*$",
                message="Username must be alphanumeric",
                code="invalid_username",
            ),
        ],
    )
    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password]
    )
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = get_user_model()
        fields = ("email", "username", "password", "password2")
        extra_kwargs = {
            "password": {"write_only": True, "min_length": 8},
        }

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError(
                {"password": "Password fields didn't match."}
            )
        return attrs

    def create(self, validated_data):
        user = self.Meta.model.objects.create(
            email=validated_data["email"],
            username=validated_data["username"],
        )
        user.set_password(validated_data["password"])
        user.save()
        return user


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        User = get_user_model()
        try:
            user = User.objects.get(email=value)
        except User.DoesNotExist:
            raise ValidationError("Email address not found.")
        if not user.is_active:
            raise ValidationError("User account is inactive.")
        return value


class ResetPasswordSerializer(serializers.Serializer):
    password1 = serializers.CharField(max_length=128)
    password2 = serializers.CharField(max_length=128)

    def validate(self, data):
        if data["password1"] != data["password2"]:
            raise ValidationError("Passwords do not match.")
        return data
