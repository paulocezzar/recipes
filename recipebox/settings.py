"""Recipe Box settings.

Environment variables (set in Render):
  SECRET_KEY            long random string (Render can generate one)
  DATABASE_URL          Postgres URL (internal URL of the StockUp database)
  DB_SCHEMA             Postgres schema for this app's tables (default: recipebox)
  ANTHROPIC_API_KEY     for reading recipe photos
  ANTHROPIC_MODEL       optional, default claude-sonnet-5
  ADMIN_USERNAME / ADMIN_PASSWORD / ADMIN_EMAIL   first login, created on start-up
"""
import os
from pathlib import Path

import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

DEBUG = os.environ.get("DEBUG", "") == "1"
SECRET_KEY = os.environ.get("SECRET_KEY") or ("dev-only-insecure-key" if DEBUG else None)
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY is not set")

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]
CSRF_TRUSTED_ORIGINS = []
render_host = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
if render_host:
    ALLOWED_HOSTS.append(render_host)
    CSRF_TRUSTED_ORIGINS.append(f"https://{render_host}")
for host in filter(None, os.environ.get("EXTRA_HOSTS", "").split(",")):
    ALLOWED_HOSTS.append(host.strip())
    CSRF_TRUSTED_ORIGINS.append(f"https://{host.strip()}")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "recipes",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "recipebox.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]
WSGI_APPLICATION = "recipebox.wsgi.application"

# --- Database -----------------------------------------------------------
# All tables live in their own Postgres schema (DB_SCHEMA), so this app can
# share a database with StockUp without touching StockUp's tables.
DB_SCHEMA = os.environ.get("DB_SCHEMA", "recipebox")
if not DB_SCHEMA.replace("_", "").isalnum():
    raise RuntimeError("DB_SCHEMA may only contain letters, digits and underscores")

if os.environ.get("DATABASE_URL"):
    db = dj_database_url.parse(os.environ["DATABASE_URL"], conn_max_age=600, conn_health_checks=True)
    db.setdefault("OPTIONS", {})["options"] = f"-c search_path={DB_SCHEMA}"
    DATABASES = {"default": db}
elif DEBUG:
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "dev.sqlite3"}}
elif os.environ.get("COLLECTSTATIC_ONLY") == "1":
    DATABASES = {"default": {"ENGINE": "django.db.backends.dummy"}}
else:
    raise RuntimeError("DATABASE_URL is not set. Add the internal URL of bakery-stock-db in Render → Environment.")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
]

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "home"
LOGOUT_REDIRECT_URL = "login"
SESSION_COOKIE_AGE = 60 * 60 * 24 * 90  # stay signed in for 90 days

LANGUAGE_CODE = "en-gb"
TIME_ZONE = "Europe/London"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

DATA_UPLOAD_MAX_MEMORY_SIZE = 25 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 25 * 1024 * 1024

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30
    SECURE_CONTENT_TYPE_NOSNIFF = True

ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}
