from .base import *

ALLOWED_HOSTS = ("*",)

CORS_ORIGIN_WHITELIST = [
    "http://localhost:3000",
    "http://127.0.0.1:8000",
    "https://loved-socially-snail.ngrok-free.app",
]

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "https://loved-socially-snail.ngrok-free.app",
]

CORS_ALLOW_CREDENTIALS = True


DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "static")
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")
