import structlog
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.staticfiles.storage import staticfiles_storage
from django.db import DatabaseError
from django.db.transaction import non_atomic_requests
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils.timezone import now
from drf_spectacular.utils import extend_schema
from rest_framework import permissions
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.response import Response

User = get_user_model()

logger = structlog.getLogger(__name__)
process_started_at = now()


@extend_schema(exclude=True)
@api_view(["GET"])
@authentication_classes([])
@permission_classes([permissions.AllowAny])
@non_atomic_requests
def index(request):
    """
    Noop.
    """
    return Response(data="Hello World.")


@non_atomic_requests
def robots(request):
    """
    Disallow bots
    """
    return HttpResponse(
        "User-agent: * \nDisallow: /",
        content_type="text/plain",
    )


@api_view(["GET", "HEAD"])
@authentication_classes([])
@permission_classes([permissions.AllowAny])
def health(request):
    """
    General app health check
    """

    healthy = True
    db_status = {}

    if settings.ENV_NAME == "testing":
        pass
    else:
        # Check db connections
        for name in settings.DATABASES.keys():
            try:
                # Trigger a simple query.
                User.objects.using(name).exists()
                pass
            except DatabaseError:
                db_status[name] = "error"
                healthy = False
                logger.exception(f"Error when connecting to db: {name}")
            else:
                db_status[name] = "ok"

    return Response(
        {
            "status": "ok" if healthy else "error",
            "db": db_status,
            "started_at": process_started_at,
        },
        status=200 if healthy else 500,
    )


@authentication_classes([])
@permission_classes([permissions.AllowAny])
@non_atomic_requests
def favicon(request):
    return redirect(staticfiles_storage.url("favicon.ico"))
