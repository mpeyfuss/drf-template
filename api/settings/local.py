from http.client import HTTPConnection

import dj_database_url

from .common import *

DEBUG = True
CORS_ALLOW_ALL_ORIGINS = True

# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases
DATABASES = {
    # Master
    "default": (
        dj_database_url.config(env="DATABASE_URL")
        | {
            "ATOMIC_REQUESTS": True,
        }
    ),
}

# See requests in console when working locally. https://stackoverflow.com/a/24588289
HTTPConnection.debuglevel = 1
