from .base import *

ALLOWED_HOSTS = ("flypgame.com",)

CORS_ORIGIN_WHITELIST = [
    "http://flypgame.com",
    "https://flypgame.com",
]

CSRF_TRUSTED_ORIGINS = [
    "https://flypgame.com",
    "http://flypgame.com",
]

CORS_ALLOW_CREDENTIALS = True


DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "static")

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")
