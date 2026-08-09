# ruff: noqa: E501
"""Common configuration for the Railway-deployed environments.

Not selected directly via ``DJANGO_SETTINGS_MODULE`` -- ``dev.py`` and ``prod.py``
import it and add their own hardcoded hosts, CORS/CSRF origins, and cookie policy.
Only secrets and Railway-injected connection strings are read from the environment;
everything else is hardcoded per environment.
"""

import logging
import ssl

import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.redis import RedisIntegration

from .base import *  # noqa: F403
from .base import INSTALLED_APPS, env

# SECRETS (environment-injected on Railway; never hardcoded)
# ------------------------------------------------------------------------------
SECRET_KEY = env("SECRET_KEY")

# DATABASES
# ------------------------------------------------------------------------------
DATABASES = {"default": env.db("DATABASE_URL")}
DATABASES["default"]["ATOMIC_REQUESTS"] = True
DATABASES["default"]["CONN_MAX_AGE"] = 0
DATABASES["default"]["CONN_HEALTH_CHECKS"] = True


def configure_db_pool(*, min_size: int, max_size: int, timeout: float) -> None:
    """Set the psycopg connection pool sizes (postgres only).

    Called by dev.py/prod.py so each environment hardcodes its own pool sizes.
    See ops/SCALING.md for how to tune them.
    """
    if DATABASES["default"]["ENGINE"] != "django.db.backends.postgresql":
        return
    DATABASES["default"]["OPTIONS"] = {
        **DATABASES["default"].get("OPTIONS", {}),
        "pool": {"min_size": min_size, "max_size": max_size, "timeout": timeout},
    }


# SESSIONS
# ------------------------------------------------------------------------------
# Read sessions from the Redis cache first, falling back to the database on a
# miss, and write to both, so sessions survive a cache flush.
SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"

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
# Both deployed environments serve a credentialed cross-origin SPA. The specific
# origins, cookie SameSite, and cookie domain are set per environment.
CORS_ALLOW_CREDENTIALS = True

# STATIC
# ------------------------------------------------------------------------------
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# EMAIL
# ------------------------------------------------------------------------------
# MAILGUN_API_KEY is a secret and stays in the environment; the sender domain and
# from-address are not secret and are hardcoded here.
MAILGUN_API_KEY = env("MAILGUN_API_KEY", default=None)
if MAILGUN_API_KEY:
    INSTALLED_APPS += ["anymail"]
    EMAIL_BACKEND = "anymail.backends.mailgun.EmailBackend"
    ANYMAIL = {
        "MAILGUN_API_KEY": MAILGUN_API_KEY,
        "MAILGUN_SENDER_DOMAIN": "mg.example.com",  # TODO: set your Mailgun sending domain
        "MAILGUN_API_URL": "https://api.mailgun.net/v3",
    }
    DEFAULT_FROM_EMAIL = "API <noreply@example.com>"  # TODO: set your from-address
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
def configure_sentry(environment: str) -> None:
    """Initialize Sentry for the given environment name.

    Called by dev.py/prod.py with a hardcoded environment so the value is known
    at import time. No-op when SENTRY_DSN is unset. The DSN is a secret and the
    release derives from the Railway-injected commit SHA, so both stay in env.
    """
    dsn = env("SENTRY_DSN", default=None)
    if not dsn:
        return
    sentry_sdk.init(
        dsn=dsn,
        environment=environment,
        release=env(
            "SENTRY_RELEASE", default=env("RAILWAY_GIT_COMMIT_SHA", default=None)
        ),
        integrations=[
            LoggingIntegration(level=logging.INFO, event_level=logging.ERROR),
            DjangoIntegration(),
            CeleryIntegration(),
            RedisIntegration(),
        ],
        traces_sample_rate=0.0,
    )
