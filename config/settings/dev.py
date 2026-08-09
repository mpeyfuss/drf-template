"""Dev-deployed settings: production hardening with cross-site auth.

Shares the common deployed config in ``_deployed.py`` and hardcodes the dev hosts
and origins, plus a SameSite=None cookie policy so a localhost frontend and preview URLs
can authenticate against the deployed dev API cross-site.
"""

from ._deployed import *  # noqa: F403
from ._deployed import configure_db_pool, configure_sentry

# DATABASES
# ------------------------------------------------------------------------------
configure_db_pool(min_size=0, max_size=4, timeout=10.0)

# HOSTS / ORIGINS
# ------------------------------------------------------------------------------
# TODO: replace the placeholder domains/ports below with the real dev values.
ALLOWED_HOSTS = [
    "api-dev.example.app",  # TODO: dev API host(s)
    "healthcheck.railway.app",
]
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",  # TODO: local frontend dev server origin(s)
    "http://localhost:3000",
]
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:5173",  # TODO: keep in sync with CORS_ALLOWED_ORIGINS
    "http://localhost:3000",
]
# Firebase Hosting preview channels (e.g. https://example-firebase-app--pr-42-ab1cd.web.app).
# TODO: replace "example-firebase-app" with your Firebase site id.
# TODO: if using netlify or vercel, you can add regexes for those as well.
CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https://example-firebase-app--[a-z0-9-]+\.web\.app$",
]

# COOKIES
# ------------------------------------------------------------------------------
# Cross-site requests (localhost or preview URLs -> deployed dev API)
# require SameSite=None, which browsers only honor with Secure (set in
# _deployed.py). The literal string "None" (not Python None) emits the
# SameSite=None attribute. Cookies are host-only since sites cannot share a
# cookie domain across origins.
SESSION_COOKIE_SAMESITE = "None"
CSRF_COOKIE_SAMESITE = "None"
SESSION_COOKIE_DOMAIN = None
CSRF_COOKIE_DOMAIN = None

# SENTRY
# ------------------------------------------------------------------------------
configure_sentry("development")
