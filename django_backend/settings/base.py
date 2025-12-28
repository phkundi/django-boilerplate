import os
from pathlib import Path
import environ
from django.core.exceptions import ImproperlyConfigured
from datetime import timedelta
import sys
from celery.schedules import crontab
from django.apps import apps as django_apps
from ..celery import app as celery_app

# Detect if running locally with SSL certificate
is_using_ssl = "--cert-file" in sys.argv

APP_NAME = "Django Boilerplate"
ADMIN_EMAIL = "email@email.com"

DEV_NOTIFICATIONS = [
    # Add your email addresses here that should receive notifications in development
]

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

environ.Env.read_env(os.path.join(BASE_DIR, ".env"))


def from_env(name, default=None):
    var = os.environ.get(name, default)
    if not var:
        if default is not None:
            print(f"WARNING!!! {name} is undefined! default value is using")
            return default
        raise ImproperlyConfigured(f"{name} is not defined in the .env file")
    return var


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = from_env("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = from_env("DEBUG_VALUE", "false") == "True"

ENVIRONMENT = from_env("ENVIRONMENT")

AUTH_USER_MODEL = "users.User"

SECURE_SSL_REDIRECT = from_env("SECURE_SSL_REDIRECT", "false") == "True"

# Update APP_URL to use HTTPS when SSL is enabled
raw_app_url = from_env("APP_URL")
raw_backend_url = from_env("BACKEND_URL")
raw_landing_url = from_env("LANDING_URL")
if is_using_ssl and raw_app_url.startswith("http://"):
    APP_URL = raw_app_url.replace("http://", "https://", 1)
    BACKEND_URL = raw_backend_url.replace("http://", "https://", 1)
    LANDING_URL = raw_landing_url.replace("http://", "https://", 1)
else:
    APP_URL = raw_app_url
    BACKEND_URL = raw_backend_url
    LANDING_URL = raw_landing_url


INSTALLED_APPS = [
    "core.apps.CoreConfig",
    "users.apps.UsersConfig",
    "notifications.apps.NotificationsConfig",
    "tracking.apps.TrackingConfig",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "django_extensions",
    "rest_framework",
    "rest_framework.authtoken",
    # OAuth
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "allauth.socialaccount.providers.apple",
    "dj_rest_auth",
    "dj_rest_auth.registration",
]

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.AllowAny",),
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
}

AUTHENTICATION_BACKENDS = [
    # "users.auth.UsernameOrEmailBackend",
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=10),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=50),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": False,
    "UPDATE_LAST_LOGIN": False,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "USER_ID_FIELD": "id",
}

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
]

LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "filters": {
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse",
        },
        "require_debug_true": {
            "()": "django.utils.log.RequireDebugTrue",
        },
    },
    "formatters": {
        "standard": {
            "format": "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            "datefmt": "%d/%b/%Y %H:%M:%S",
        },
        "colored": {
            "()": "django_backend.utils.colored_logging.DevelopmentFormatter",
            "format": "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            "datefmt": "%d/%b/%Y %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "standard",
        },
        "mail_admins": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "django.utils.log.AdminEmailHandler",
        },
    },
    "loggers": {
        logger_name: {
            "handlers": ["console", "mail_admins"],
            "level": "ERROR",
            "propagate": True,
        }
        for logger_name in (
            "root",
            "django_backend",
            "tracking",
            "notifications",
            "root",
            "celery",
            "django",
            "django.request",
            "django.db.backends",
            "django.template",
        )
    },
}

ROOT_URLCONF = "django_backend.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            os.path.join(BASE_DIR, "notifications/emails/users/templates"),
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "django_backend.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "HOST": from_env("POSTGRESQL_HOST", ""),
        "PORT": from_env("POSTGRESQL_PORT", "5432"),
        "NAME": from_env("POSTGRESQL_NAME", ""),
        "USER": from_env("POSTGRESQL_USER", ""),
        "PASSWORD": from_env("POSTGRESQL_PASSWORD", ""),
        "CONN_MAX_AGE": 0,
    },
}


# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Redis
CELERY_TIMEZONE = "Europe/Paris"
CELERY_BROKER_URL = os.environ.get("REDIS_URL")
CELERY_RESULT_BACKEND = os.environ.get("REDIS_URL")
CELERY_IMPORTS = ("app.services",)
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"

celery_app.autodiscover_tasks(lambda: [n.name for n in django_apps.get_app_configs()])
celery_app.conf.broker_transport_options = {
    "visibility_timeout": 3600,
    "broker_connection_retry_on_startup": True,
}  # 1 hour to avoid task being started twice back to back

celery_app.conf.beat_schedule = {
    # Clean up notifications every day at 9:05 AM
    "clean_up_notifications": {
        "task": "notifications.tasks.clean_up_notifications",
        "schedule": crontab(hour=9, minute=5),
    },
}


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True


# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Zeptomail Email Service
ZEPTOMAIL_FROM_EMAIL = from_env("ZEPTOMAIL_FROM_EMAIL")
ZEPTOMAIL_TOKEN = from_env("ZEPTOMAIL_TOKEN")
ZEPTOMAIL_WEBHOOK_SECRET = from_env("ZEPTOMAIL_WEBHOOK_SECRET")

# Firebase Push Notifications
VAPID_PRIVATE_KEY = from_env("VAPID_PRIVATE_KEY")

# Stripe
STRIPE_SECRET_KEY = from_env("STRIPE_SECRET_KEY")
STRIPE_PUBLISHABLE_KEY = from_env("STRIPE_PUBLISHABLE_KEY")
STRIPE_WEBHOOK_SECRET = from_env("STRIPE_WEBHOOK_SECRET")

POSTHOG_API_KEY = from_env("POSTHOG_API_KEY")
POSTHOG_HOST = from_env("POSTHOG_HOST")


# Email verification token expiration time in seconds (default: 7 days)
# VERIFICATION_TOKEN_EXPIRATION_TIME = 60 * 60 * 24 * 7  # 7 days
VERIFICATION_TOKEN_EXPIRATION_TIME = 1110  # 10 seconds for development

VAPID_PRIVATE_KEY = from_env("VAPID_PRIVATE_KEY")

SITE_ID = 1

# Google OAuth settings
GOOGLE_OAUTH2_CLIENT_ID = from_env("GOOGLE_OAUTH2_CLIENT_ID")
GOOGLE_OAUTH2_CLIENT_SECRET = from_env("GOOGLE_OAUTH2_CLIENT_SECRET")

# Apple OAuth settings
APPLE_WEB_CLIENT_ID = from_env("APPLE_WEB_CLIENT_ID")  # Service ID for web
APPLE_NATIVE_CLIENT_ID = from_env("APPLE_NATIVE_CLIENT_ID")  # App ID for native
APPLE_TEAM_ID = from_env("APPLE_TEAM_ID")
APPLE_KEY_ID = from_env("APPLE_KEY_ID")
APPLE_PRIVATE_KEY = from_env("APPLE_PRIVATE_KEY").replace("\\n", "\n")

# List of valid Apple client IDs for token verification
APPLE_VALID_CLIENT_IDS = [
    APPLE_WEB_CLIENT_ID,
    APPLE_NATIVE_CLIENT_ID,
]
# Remove None values
APPLE_VALID_CLIENT_IDS = [cid for cid in APPLE_VALID_CLIENT_IDS if cid]

# AllAuth settings (updated format)
ACCOUNT_EMAIL_VERIFICATION = "none"
ACCOUNT_USER_MODEL_USERNAME_FIELD = None  # No username field, using email instead
ACCOUNT_USER_MODEL_EMAIL_FIELD = "email"
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_SESSION_REMEMBER = None
ACCOUNT_DEFAULT_HTTP_PROTOCOL = "https" if not DEBUG else "http"

# Modern allauth settings
ACCOUNT_LOGIN_METHODS = {"email"}  # Use email for authentication
ACCOUNT_SIGNUP_FIELDS = [
    "email*",
    "password1*",
]  # Removed username* since we don't use it

# Social account settings
SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "SCOPE": [
            "profile",
            "email",
        ],
        "AUTH_PARAMS": {
            "access_type": "online",
        },
        "OAUTH_PKCE_ENABLED": True,
        "APP": {
            "client_id": GOOGLE_OAUTH2_CLIENT_ID,
            "secret": GOOGLE_OAUTH2_CLIENT_SECRET,
        },
    },
    "apple": {
        "APP": {
            "client_id": APPLE_WEB_CLIENT_ID,  # Use web client ID for allauth fallback
            "secret": APPLE_PRIVATE_KEY,
            "key": APPLE_KEY_ID,
            "team": APPLE_TEAM_ID,
        }
    },
}

# dj-rest-auth settings
REST_AUTH = {
    "USE_JWT": True,
    "JWT_AUTH_COOKIE": None,
    "JWT_AUTH_REFRESH_COOKIE": None,
    "JWT_AUTH_HTTPONLY": False,
    "JWT_AUTH_SAMESITE": "Lax",
    "JWT_AUTH_SECURE": not DEBUG,
    "JWT_AUTH_RETURN_EXPIRATION": True,
    "JWT_TOKEN_CLAIMS_SERIALIZER": "users.serializers.auth.CustomTokenObtainPairSerializer",
    "JWT_SERIALIZER": "users.serializers.auth.CustomTokenObtainPairSerializer",
    "JWT_SERIALIZER_WITH_EXPIRATION": "users.serializers.auth.CustomTokenObtainPairSerializer",
    "USER_DETAILS_SERIALIZER": "users.serializers.users.UserBaseSerializer",
    "LOGIN_SERIALIZER": "users.serializers.auth.CustomTokenObtainPairSerializer",
    "TOKEN_MODEL": None,  # Disable DRF tokens since we use JWT
}

# Custom user adapter for allauth
SOCIALACCOUNT_ADAPTER = "users.adapters.CustomSocialAccountAdapter"
