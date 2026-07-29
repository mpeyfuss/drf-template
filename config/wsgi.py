"""WSGI config for the API."""

import os

from django.core.wsgi import get_wsgi_application

if "DJANGO_SETTINGS_MODULE" not in os.environ:
    msg = "DJANGO_SETTINGS_MODULE must be set before starting the WSGI application."
    raise RuntimeError(msg)

application = get_wsgi_application()
