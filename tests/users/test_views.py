from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from django.conf import settings
from django.urls import reverse
from rest_framework import status

if TYPE_CHECKING:
    from rest_framework.test import APIClient


@pytest.mark.django_db
class TestCsrfView:
    def test_returns_token_and_sets_cookie(self, api_client: APIClient):
        response = api_client.get(reverse("users:csrf"))

        assert response.status_code == status.HTTP_200_OK
        assert response.data["csrfToken"]

        cookie = response.cookies[settings.CSRF_COOKIE_NAME]
        assert cookie.value
        # The SPA must be able to read the token, so the cookie is not HttpOnly.
        assert not cookie["httponly"]

    def test_is_public(self, api_client: APIClient):
        # No authentication is required to bootstrap the CSRF token.
        response = api_client.get(reverse("users:csrf"))

        assert response.status_code == status.HTTP_200_OK
