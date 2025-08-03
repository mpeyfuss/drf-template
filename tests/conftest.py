import pytest
from rest_framework.test import APIClient


@pytest.fixture()
def vcr_config():
    """
    https://github.com/kiwicom/pytest-recording
    """
    return {
        "record_mode": "once",
        "decode_compressed_response": True,
        "filter_headers": [
            ("authorization", "XXX"),
            ("x-api-key", "XXX"),
            ("x-goog-api-key", "XXX"),
        ],
        "filter_query_parameters": [
            ("apikey", "XXX"),
            ("api_key", "XXX"),
            ("pinataGatewayToken", "XXX"),
        ],
    }


@pytest.fixture()
def api_client():
    return APIClient(enforce_csrf_checks=True)


@pytest.fixture()
def auth_client(api_client: APIClient) -> APIClient:
    # update the following to login as a user so you can test authenticated endpoints easily
    return api_client
