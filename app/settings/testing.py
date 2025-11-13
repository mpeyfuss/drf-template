import logging

import structlog

from .common import *

DEBUG = True

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    },
}


STORAGES["staticfiles"] = {  # noqa: F405
    "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
}

WHITENOISE_AUTOREFRESH = True

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "plain_console": {
            "()": structlog.stdlib.ProcessorFormatter,
            "processor": structlog.dev.ConsoleRenderer(),
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "plain_console",
        },
        "null": {
            "class": "logging.NullHandler",
        },
    },
    "loggers": {
        "django_structlog": {
            "handlers": ["console"],
            "level": "DEBUG",
        },
    },
    "root": {
        "level": logging.DEBUG,
        "handlers": ["console"],
    },
}
