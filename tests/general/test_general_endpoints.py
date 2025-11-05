import pytest

pytestmark = [pytest.mark.django_db(databases="__all__")]


def test_index(api_client):
    response = api_client.get("/")

    assert response.status_code == 200


def test_health(api_client):
    response = api_client.get("/health")

    assert response.status_code == 200 and response.data["status"] == "ok"
