import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from tests.factories import UserFactory

User = get_user_model()

pytestmark = [pytest.mark.django_db()]


def test_get_user(api_client: APIClient):
    # create users
    user_one = UserFactory()
    user_two = UserFactory()

    # get user one
    r = api_client.get(f"/users/{user_one.id}")
    assert r.status_code == 200 and r.data["username"] == user_one.username

    # get user two
    r = api_client.get(f"/users/{user_two.id}")
    assert r.status_code == 200 and r.data["username"] == user_two.username

    # get 404
    r = api_client.get("/users/3")
    assert r.status_code == 404
