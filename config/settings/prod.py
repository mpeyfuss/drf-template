"""Production settings for the Railway-deployed API.

Shares the common deployed config in ``_deployed.py`` and hardcodes the
production hosts, CORS/CSRF origins, and same-site apex cookie policy. Only
secrets and Railway-injected connection strings come from the environment.
"""

from ._deployed import *  # noqa: F403
from ._deployed import configure_db_pool, configure_sentry

# DATABASES
# ------------------------------------------------------------------------------
configure_db_pool(min_size=0, max_size=4, timeout=10.0)

# HOSTS / ORIGINS
# ------------------------------------------------------------------------------
# TODO: replace the placeholder domains below with the real production values.
ALLOWED_HOSTS = [
    "api.example.app",  # TODO: production API host(s)
    "healthcheck.railway.app",
]
CORS_ALLOWED_ORIGINS = [
    "https://app.example.app",  # TODO: production frontend origin(s)
]
CSRF_TRUSTED_ORIGINS = [
    "https://app.example.app",  # TODO: keep in sync with CORS_ALLOWED_ORIGINS
]
CORS_ALLOWED_ORIGIN_REGEXES: list[str] = []

# COOKIES
# ------------------------------------------------------------------------------
# The frontend and API live on subdomains of a shared apex (e.g. app. and api.),
# so Lax cookies scoped to the apex domain are sent on same-site subdomain
# requests. The __Secure- cookie names are compatible with a Domain attribute
# (only __Host- forbids it). CORS still applies because the subdomains are
# distinct origins.
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_DOMAIN = (
    ".example.app"  # TODO: apex domain shared by the frontend and API
)
CSRF_COOKIE_DOMAIN = ".example.app"  # TODO: keep in sync with SESSION_COOKIE_DOMAIN

# SENTRY
# ------------------------------------------------------------------------------
configure_sentry("production")
