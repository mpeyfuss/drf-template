# ruff: noqa: E501
"""Settings shared by all Railway-deployed environments (dev + production)."""

import logging
import ssl

import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.redis import RedisIntegration

from .base import *  # noqa: F403
from .base import INSTALLED_APPS, env

# GENERAL
# ------------------------------------------------------------------------------
SECRET_KEY = env("SECRET_KEY")
ALLOWED_HOSTS = [
    *env.list("DJANGO_ALLOWED_HOSTS"),
    "healthcheck.railway.app",
]
CORS_ALLOWED_ORIGINS: list[str] = env.list("CORS_ALLOWED_ORIGINS", default=[])
CSRF_TRUSTED_ORIGINS: list[str] = env.list("CSRF_TRUSTED_ORIGINS", default=[])

# DATABASES
# ------------------------------------------------------------------------------
DATABASES = {"default": env.db("DATABASE_URL")}
DATABASES["default"]["ATOMIC_REQUESTS"] = True
DATABASES["default"]["CONN_MAX_AGE"] = 0
DATABASES["default"]["CONN_HEALTH_CHECKS"] = True
if DATABASES["default"]["ENGINE"] == "django.db.backends.postgresql":
    DATABASES["default"]["OPTIONS"] = {
        **DATABASES["default"].get("OPTIONS", {}),
        "pool": {
            "min_size": env.int("DATABASE_POOL_MIN_SIZE", default=0),
            "max_size": env.int("DATABASE_POOL_MAX_SIZE", default=4),
            "timeout": env.float("DATABASE_POOL_TIMEOUT", default=10.0),
        },
    }

# REDIS / CELERY
# ------------------------------------------------------------------------------
REDIS_URL = env("REDIS_URL")
REDIS_SSL = REDIS_URL.startswith("rediss://")
CELERY_BROKER_URL = REDIS_URL
CELERY_BROKER_USE_SSL = {"ssl_cert_reqs": ssl.CERT_REQUIRED} if REDIS_SSL else None

# CACHES
# ------------------------------------------------------------------------------
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "IGNORE_EXCEPTIONS": False,
        },
    },
}

# SECURITY
# ------------------------------------------------------------------------------
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
# Railway's internal health check hits the container over plain HTTP (no
# X-Forwarded-Proto), so exempt it from the HTTPS redirect to avoid a 301.
SECURE_REDIRECT_EXEMPT = [r"^health$"]
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_NAME = "__Secure-sessionid"
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_NAME = "__Secure-csrftoken"
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# STATIC
# ------------------------------------------------------------------------------
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# EMAIL
# ------------------------------------------------------------------------------
MAILGUN_API_KEY = env("MAILGUN_API_KEY", default=None)
if MAILGUN_API_KEY:
    INSTALLED_APPS += ["anymail"]
    EMAIL_BACKEND = "anymail.backends.mailgun.EmailBackend"
    ANYMAIL = {
        "MAILGUN_API_KEY": MAILGUN_API_KEY,
        "MAILGUN_SENDER_DOMAIN": env("MAILGUN_DOMAIN"),
        "MAILGUN_API_URL": "https://api.mailgun.net/v3",
    }
    DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL")
    SERVER_EMAIL = DEFAULT_FROM_EMAIL
    EMAIL_SUBJECT_PREFIX = ""

# LOGGING
# ------------------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s",
        },
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {"level": "INFO", "handlers": ["console"]},
    "loggers": {
        "django.db.backends": {
            "level": "ERROR",
            "handlers": ["console"],
            "propagate": False,
        },
        "sentry_sdk": {"level": "ERROR", "handlers": ["console"], "propagate": False},
        "django.security.DisallowedHost": {
            "level": "ERROR",
            "handlers": ["console"],
            "propagate": False,
        },
        "django.request": {
            "level": "WARNING",
            "handlers": ["console"],
            "propagate": False,
        },
    },
}

# SENTRY
# ------------------------------------------------------------------------------
SENTRY_DSN = env("SENTRY_DSN", default=None)
if SENTRY_DSN:
    SENTRY_ENVIRONMENT = env(
        "SENTRY_ENVIRONMENT",
        default=env("RAILWAY_ENVIRONMENT_NAME", default="deployed"),
    )
    SENTRY_RELEASE = env(
        "SENTRY_RELEASE",
        default=env("RAILWAY_GIT_COMMIT_SHA", default=None),
    )
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        environment=SENTRY_ENVIRONMENT,
        release=SENTRY_RELEASE,
        integrations=[
            LoggingIntegration(level=logging.INFO, event_level=logging.ERROR),
            DjangoIntegration(),
            CeleryIntegration(),
            RedisIntegration(),
        ],
        traces_sample_rate=0.0,
    )
