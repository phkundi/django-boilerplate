from .base import *
from storages.backends.s3boto3 import S3Boto3Storage

ALLOWED_HOSTS = (APP_URL, LANDING_URL)

CORS_ORIGIN_WHITELIST = [
    APP_URL, LANDING_URL
]

CSRF_TRUSTED_ORIGINS = [
    APP_URL, LANDING_URL
]

CORS_ALLOW_CREDENTIALS = True


class StaticStorage(S3Boto3Storage):
    location = "static"
    default_acl = None
    file_overwrite = True


class MediaStorage(S3Boto3Storage):
    location = "media"
    default_acl = None
    file_overwrite = False


AWS_ACCESS_KEY_ID = from_env("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = from_env("AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = from_env("AWS_STORAGE_BUCKET_NAME")
AWS_S3_CUSTOM_DOMAIN = f"{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com"
AWS_S3_REGION_NAME = from_env("AWS_S3_REGION_NAME")


AWS_S3_OBJECT_PARAMETERS = {
    "CacheControl": "max-age=86400",  # 24 hours of cache
}
AWS_QUERYSTRING_AUTH = False
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = None


STATICFILES_STORAGE = "flyp_backend.settings.production.StaticStorage"
DEFAULT_FILE_STORAGE = "flyp_backend.settings.production.MediaStorage"

STATIC_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/static/"
MEDIA_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/media/"


STATIC_ROOT = "static/"
MEDIA_ROOT = "media/"
