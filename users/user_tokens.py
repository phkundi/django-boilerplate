from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.conf import settings
import time


class TokenExpired(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class VerificationTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return (
            str(user.pk)
            + str(user.email)
            + str(timestamp)
            + str(user.is_active)
            + str(settings.SECRET_KEY)
        )

    def make_token(self, user):
        timestamp = str(int(time.time()))
        hash_value = self._make_hash_value(user, timestamp)
        hash_value_bytes = hash_value.encode("utf-8")
        token = urlsafe_base64_encode(hash_value_bytes)
        print(token)
        return token + "-" + timestamp

    def check_token(self, user, token):
        if not (user and token):
            return False
        try:
            only_token = token.split("-")[0]
            timestamp = token.split("-")[1]
            hash_value = urlsafe_base64_decode(only_token)
        except (TypeError, ValueError, OverflowError):
            return False
        if (
            int(time.time()) - int(timestamp)
        ) > settings.VERIFICATION_TOKEN_EXPIRATION_TIME:
            raise TokenExpired(
                "Your activation link has expired, please click on the button below to receive a new one."
            )
        expected_value = self._make_hash_value(user, timestamp)
        return expected_value == hash_value.decode("utf-8")
