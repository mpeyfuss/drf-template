"""
WSGI config for the artcade project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/wsgi/
"""

import environ
from django.core.wsgi import get_wsgi_application

# Load Environment Variables
env = environ.Env()
environ.Env.read_env(".env")

application = get_wsgi_application()
