import os
from pathlib import Path
import environ
from django.core.exceptions import ImproperlyConfigured
from datetime import timedelta
import sys

# Detect if running locally with SSL certificate
is_using_ssl = "--cert-file" in sys.argv

APP_NAME = "Django Boilerplate"
ADMIN_EMAIL = "email@email.com"

DEV_NOTIFICATIONS = [
    "pk@pkundr.com",
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
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "django_extensions",
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
        "DIRS": [],
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
CELERY_BROKER_URL = os.environ.get("REDIS_URL")
CELERY_RESULT_BACKEND = os.environ.get("REDIS_URL")
CELERY_IMPORTS = ("app.services",)
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"

# Email
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = from_env("EMAIL_HOST")
EMAIL_PORT = from_env("EMAIL_PORT")
EMAIL_USE_TLS = from_env("EMAIL_USE_TLS", "false") == "True"
EMAIL_HOST_USER = from_env("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = from_env("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = from_env("DEFAULT_FROM_EMAIL")


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

# Firebase Push Notifications
VAPID_PRIVATE_KEY = from_env("VAPID_PRIVATE_KEY")