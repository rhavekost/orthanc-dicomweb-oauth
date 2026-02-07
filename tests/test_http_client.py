"""Tests for HTTP client interface."""
import pytest
import requests
import responses

from src.http_client import HttpResponse, RequestsHttpClient


class TestHttpResponse:
    """Test HttpResponse dataclass."""

    def test_http_response_creation(self):
        response = HttpResponse(
            status_code=200,
            json_data={"access_token": "test"},
            text="response text",
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 200
        assert response.json_data == {"access_token": "test"}
        assert response.text == "response text"
        assert response.headers["Content-Type"] == "application/json"


class TestRequestsHttpClient:
    """Test default requests-based HTTP client."""

    @responses.activate
    def test_post_success(self):
        responses.add(
            responses.POST,
            "https://login.example.com/token",
            json={"access_token": "test_token"},
            status=200,
        )

        client = RequestsHttpClient()
        response = client.post(
            url="https://login.example.com/token",
            data={"grant_type": "client_credentials"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            verify=True,
            timeout=30,
        )

        assert response.status_code == 200
        assert response.json_data == {"access_token": "test_token"}

    @responses.activate
    def test_post_timeout(self):
        responses.add(
            responses.POST,
            "https://login.example.com/token",
            body=requests.Timeout(),
        )

        client = RequestsHttpClient()

        with pytest.raises(requests.Timeout):
            client.post(
                url="https://login.example.com/token",
                data={"grant_type": "client_credentials"},
                verify=True,
            )

    @responses.activate
    def test_get_success(self):
        responses.add(
            responses.GET,
            "https://login.example.com/keys",
            json={"keys": [{"kid": "key1"}]},
            status=200,
        )

        client = RequestsHttpClient()
        response = client.get(
            url="https://login.example.com/keys", verify=True, timeout=10
        )

        assert response.status_code == 200
        assert response.json_data == {"keys": [{"kid": "key1"}]}
