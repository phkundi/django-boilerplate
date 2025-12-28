from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model
import re


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def save_user(self, request, sociallogin, form=None):
        """
        Save a new user from social login, generating a unique username from email
        """
        user = sociallogin.user
        user_model = get_user_model()

        if user.pk:
            return user

        # Get email from social account data
        email = user.email
        if not email and sociallogin.account.extra_data:
            email = sociallogin.account.extra_data.get("email")

        # Generate username from email
        # if email:
        #     base_username = email.split("@")[0]
        #     # Clean the username to contain only alphanumeric characters
        #     base_username = re.sub(r"[^a-zA-Z0-9]", "", base_username)

        #     # Ensure username is unique
        #     username = base_username
        #     counter = 1
        #     while user_model.objects.filter(username=username).exists():
        #         username = f"{base_username}{counter}"
        #         counter += 1

        #     user.username = username.lower()

        # Set default fields
        user.email = email.lower() if email else ""
        user.is_active = True

        # Get additional data from Google profile
        extra_data = sociallogin.account.extra_data
        if extra_data:
            user.first_name = extra_data.get("given_name", "")
            user.last_name = extra_data.get("family_name", "")

        user.save()
        return user

    def pre_social_login(self, request, sociallogin):
        """
        Invoked just before the social account is logged in.
        This is used to connect existing users with social accounts.
        """
        # Check if a user with this email already exists
        if sociallogin.account.provider == "google":
            email = sociallogin.account.extra_data.get("email")
            if email:
                try:
                    user_model = get_user_model()
                    existing_user = user_model.objects.get(email=email)
                    # Connect the social account to the existing user
                    sociallogin.connect(request, existing_user)
                except user_model.DoesNotExist:
                    pass
