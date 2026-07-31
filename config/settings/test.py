"""Settings optimized for test speed."""

from .base import *  # noqa: F403
from .base import MIDDLEWARE, env

# MIDDLEWARE
# ------------------------------------------------------------------------------
MIDDLEWARE = [
    m for m in MIDDLEWARE if m != "whitenoise.middleware.WhiteNoiseMiddleware"
]

# DATABASES
# ------------------------------------------------------------------------------
DATABASES = {
    "default": env.db("DATABASE_URL", default="sqlite://:memory:"),
}
DATABASES["default"]["ATOMIC_REQUESTS"] = True

# GENERAL
# ------------------------------------------------------------------------------
SECRET_KEY = env(
    "DJANGO_SECRET_KEY",
    default="LYDQI8cEwe1JFqjKjMET71NVXOzap1yUHyanuVGqNVuWIjU124G1pHZpMCCdbTAZ",
)
TEST_RUNNER = "django.test.runner.DiscoverRunner"

# PASSWORDS
# ------------------------------------------------------------------------------
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# EMAIL
# ------------------------------------------------------------------------------
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# CORS
# ------------------------------------------------------------------------------
CORS_ALLOW_ALL_ORIGINS = True

# CELERY
# ------------------------------------------------------------------------------
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
