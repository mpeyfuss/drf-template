from typing import TYPE_CHECKING

import pytest
from django.db import OperationalError
from rest_framework import status

from apps.general import views

if TYPE_CHECKING:
    from rest_framework.test import APIClient


@pytest.mark.django_db
class TestIndexView:
    def test_authenticated(self, auth_client: APIClient):
        response = auth_client.get("/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data == "Hello World."

    def test_unauthenticated(self, api_client: APIClient):
        response = api_client.get("/")
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestHealthView:
    def test_database_is_ready(self, api_client: APIClient):
        response = api_client.get("/health")
        assert response.status_code == status.HTTP_200_OK
        assert response.data == {"status": "ok"}

    def test_database_is_unavailable(self, api_client: APIClient, monkeypatch):
        def unavailable_cursor():
            msg = "database unavailable"
            raise OperationalError(msg)

        monkeypatch.setattr(views.connection, "cursor", unavailable_cursor)

        response = api_client.get("/health")
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert response.data == {"status": "unavailable"}


class TestPageNotFound:
    def test_unmatched_route_returns_standard_json_error(self, api_client: APIClient):
        response = api_client.get("/missing")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.headers["Content-Type"] == "application/json"
        assert response.json() == {
            "type": "client_error",
            "errors": [
                {
                    "code": "not_found",
                    "detail": "Not found.",
                    "attr": None,
                },
            ],
        }
