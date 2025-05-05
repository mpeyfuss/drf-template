import pytest
from rest_framework.test import APIClient


@pytest.fixture()
def api_client():
    return APIClient(enforce_csrf_checks=True)


@pytest.fixture()
def auth_client(api_client: APIClient) -> APIClient:
    # update the following to login as a user so you can test authenticated endpoints easily
    return api_client
