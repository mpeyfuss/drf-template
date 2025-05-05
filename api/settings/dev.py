# import re

import dj_database_url

from .common import *

# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases
DATABASES = {
    "default": (
        dj_database_url.config(env="DATABASE_URL")
        | {
            "ATOMIC_REQUESTS": True,
        }
    ),
}

# Override log level
LOGGING["root"]["level"] = logging.WARNING  # noqa
LOGGING["loggers"]["django_structlog"]["level"] = logging.WARNING  # noqa

# CORS
CORS_ALLOW_ALL_ORIGINS = True

# CSRF
CSRF_TRUSTED_ORIGINS = [
    # TODO - add trusted origins here
]

# Allow django to detect if request was made via https.
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
