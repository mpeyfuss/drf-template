from .base import *  # noqa: F403
from .base import INSTALLED_APPS, env

# GENERAL
# ------------------------------------------------------------------------------
DEBUG = True
SECRET_KEY = env(
    "DJANGO_SECRET_KEY",
    default="WZ79672g9w14z2dYv2rLIxfdr2s9ycufHpLcDtoq4BdHXC0FjZe2JTdSF6kLVefY",
)
ALLOWED_HOSTS = ["localhost", "0.0.0.0", "127.0.0.1"]  # noqa: S104

# CACHES
# ------------------------------------------------------------------------------
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "",
    },
}

# EMAIL
# ------------------------------------------------------------------------------
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# CORS
# ------------------------------------------------------------------------------
CORS_ALLOW_ALL_ORIGINS = True

# CELERY
# ------------------------------------------------------------------------------
CELERY_TASK_ALWAYS_EAGER = env.bool("CELERY_TASK_ALWAYS_EAGER", default=True)
CELERY_TASK_EAGER_PROPAGATES = True

# WHITENOISE
# ------------------------------------------------------------------------------
INSTALLED_APPS = ["whitenoise.runserver_nostatic", *INSTALLED_APPS]

# MIGRATION LINTER
# ------------------------------------------------------------------------------
# Provides the `lintmigrations` command for checking migrations locally before
# pushing. Dev-only app; never installed in deployed settings.
INSTALLED_APPS += ["django_migration_linter"]
