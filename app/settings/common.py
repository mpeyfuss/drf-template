import logging
import os
from pathlib import Path

import environ
import structlog

logger = structlog.getLogger(__name__)

DEBUG = False
APPEND_SLASH = False

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load Environment Variables
env = environ.Env()
env.read_env(BASE_DIR / ".env")

ENV_NAME = os.getenv("DJANGO_SETTINGS_MODULE").split(".")[-1]  # e.g. local, dev, prod

# Environment secrets
SECRET_KEY = env("SECRET_KEY")
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")

# Hardcoded values

# Application definition
INSTALLED_APPS = [
    "whitenoise.runserver_nostatic",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
    # third party apps
    "corsheaders",
    "drf_spectacular",
    "drf_standardized_errors",
    "rest_framework",
    "rest_framework.authtoken",
    "django_structlog",
    # your apps
    "users",
]

# custom user model
AUTH_USER_MODEL = "users.User"

MIDDLEWARE = [
    "app.middleware.HealthCheckMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_structlog.middlewares.RequestMiddleware",
]

ROOT_URLCONF = "app.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "app/templates"],
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

WSGI_APPLICATION = "app.wsgi.application"

# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators
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


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/
LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "collectstatic"
STATICFILES_DIRS = [BASE_DIR / "app/static"]

# Storages
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Logging for dev/production/etc. Overriden in local, testing
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
            "level": logging.INFO,
        },
    },
    "root": {
        "level": logging.INFO,
        "handlers": ["console"],
    },
}

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.filter_by_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)


# DRF
# https://www.django-rest-framework.org/api-guide/settings/
REST_FRAMEWORK = {
    # https://www.django-rest-framework.org/api-guide/authentication/
    # TODO - update these classes
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.BasicAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    # https://www.django-rest-framework.org/api-guide/pagination/
    "DEFAULT_PAGINATION_CLASS": "app.pagination.ApiPagination",
    "ORDERING_PARAM": "order",
    # https://www.django-rest-framework.org/api-guide/testing/
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
    # https://drf-standardized-errors.readthedocs.io/
    "DEFAULT_SCHEMA_CLASS": "drf_standardized_errors.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "drf_standardized_errors.handler.exception_handler",
}

# CSRF
# https://docs.djangoproject.com/en/5.2/ref/csrf/
CSRF_TRUSTED_ORIGINS = []  # overwrite in specific envs
CSRF_COOKIE_SAMESITE = "None"
CSRF_COOKIE_SECURE = True

# CORS
# https://github.com/adamchainz/django-cors-headers
CORS_ALLOWED_ORIGINS = []
CORS_ALLOW_CREDENTIALS = True


# https://drf-standardized-errors.readthedocs.io/en/latest/settings.html
DRF_STANDARDIZED_ERRORS = {
    "EXCEPTION_FORMATTER_CLASS": "utils.formatters.FilteredExceptionFormatter",
    "ENABLE_IN_DEBUG_FOR_UNHANDLED_EXCEPTIONS": True,
    "ALLOWED_ERROR_STATUS_CODES": [
        "400",  # Bad Request
        "401",  # Unauthorized
        "403",  # Forbidden
        "404",  # Not Found
        "405",  # Method Not Allowed
        "406",  # Not Acceptable
        "409",  # Conflict
        "415",  # Unsupported Media Type
        "429",  # Too Many Requests
        "500",  # Internal Server Error
    ],
}

# https://drf-spectacular.readthedocs.io/en/latest/settings.html
SPECTACULAR_SETTINGS = {
    "TITLE": "API",
    "DESCRIPTION": "",
    "VERSION": "1.0.0",
    "SWAGGER_UI_FAVICON_HREF": "/favicon.ico",
    "SCHEMA_PATH_PREFIX": r"/v[0-9]/",
    "SERVE_PERMISSIONS": ["rest_framework.permissions.AllowAny"],
    "POSTPROCESSING_HOOKS": [
        "drf_standardized_errors.openapi_hooks.postprocess_schema_enums"
    ],
    "ENUM_NAME_OVERRIDES": {
        "ValidationErrorEnum": "drf_standardized_errors.openapi_serializers.ValidationErrorEnum.choices",
        "ClientErrorEnum": "drf_standardized_errors.openapi_serializers.ClientErrorEnum.choices",
        "ServerErrorEnum": "drf_standardized_errors.openapi_serializers.ServerErrorEnum.choices",
        "ErrorCode401Enum": "drf_standardized_errors.openapi_serializers.ErrorCode401Enum.choices",
        "ErrorCode403Enum": "drf_standardized_errors.openapi_serializers.ErrorCode403Enum.choices",
        "ErrorCode404Enum": "drf_standardized_errors.openapi_serializers.ErrorCode404Enum.choices",
        "ErrorCode405Enum": "drf_standardized_errors.openapi_serializers.ErrorCode405Enum.choices",
        "ErrorCode406Enum": "drf_standardized_errors.openapi_serializers.ErrorCode406Enum.choices",
        "ErrorCode415Enum": "drf_standardized_errors.openapi_serializers.ErrorCode415Enum.choices",
        "ErrorCode429Enum": "drf_standardized_errors.openapi_serializers.ErrorCode429Enum.choices",
        "ErrorCode500Enum": "drf_standardized_errors.openapi_serializers.ErrorCode500Enum.choices",
    },
}
