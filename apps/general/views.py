import logging

from django.db import DatabaseError, connection, transaction
from django.http import HttpRequest, JsonResponse
from django.utils.decorators import method_decorator
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger(__name__)


def page_not_found(_request: HttpRequest, exception: Exception) -> JsonResponse:
    del exception
    return JsonResponse(
        {
            "type": "client_error",
            "errors": [
                {
                    "code": "not_found",
                    "detail": "Not found.",
                    "attr": None,
                },
            ],
        },
        status=404,
    )


class HealthSerializer(serializers.Serializer):
    status = serializers.CharField()


class IndexView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(responses={200: OpenApiTypes.STR}, auth=[])
    def get(self, request):
        return Response("Hello World.")


@method_decorator(transaction.non_atomic_requests, name="dispatch")
class HealthView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(
        responses={200: HealthSerializer, 503: HealthSerializer},
        auth=[],
    )
    def get(self, request):
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
        except DatabaseError:
            logger.exception("Database readiness check failed.")
            return Response({"status": "unavailable"}, status=503)
        return Response({"status": "ok"})
