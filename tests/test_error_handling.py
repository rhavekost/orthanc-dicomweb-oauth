import pytest
import responses
from requests.exceptions import Timeout, ConnectionError
from src.token_manager import TokenManager, TokenAcquisitionError


@responses.activate
def test_retry_on_timeout():
    """Test that token acquisition retries on timeout."""
    # First attempt times out
    responses.add(
        responses.POST,
        "https://login.example.com/oauth2/token",
        body=Timeout("Connection timeout")
    )

    # Second attempt succeeds
    responses.add(
        responses.POST,
        "https://login.example.com/oauth2/token",
        json={
            "access_token": "token123",
            "token_type": "Bearer",
            "expires_in": 3600
        },
        status=200
    )

    config = {
        "TokenEndpoint": "https://login.example.com/oauth2/token",
        "ClientId": "client123",
        "ClientSecret": "secret456",
        "Scope": "scope"
    }

    manager = TokenManager("test-server", config)
    token = manager.get_token()

    assert token == "token123"
    assert len(responses.calls) == 2  # Retried once


@responses.activate
def test_max_retries_exceeded():
    """Test that token acquisition fails after max retries."""
    # All attempts time out
    for _ in range(3):
        responses.add(
            responses.POST,
            "https://login.example.com/oauth2/token",
            body=Timeout("Connection timeout")
        )

    config = {
        "TokenEndpoint": "https://login.example.com/oauth2/token",
        "ClientId": "client123",
        "ClientSecret": "secret456",
        "Scope": "scope"
    }

    manager = TokenManager("test-server", config)

    with pytest.raises(TokenAcquisitionError, match="after 3 attempts"):
        manager.get_token()

    assert len(responses.calls) == 3  # All retries attempted


@responses.activate
def test_no_retry_on_auth_error():
    """Test that 401 authentication errors are not retried."""
    responses.add(
        responses.POST,
        "https://login.example.com/oauth2/token",
        json={"error": "invalid_client"},
        status=401
    )

    config = {
        "TokenEndpoint": "https://login.example.com/oauth2/token",
        "ClientId": "invalid_client",
        "ClientSecret": "wrong_secret",
        "Scope": "scope"
    }

    manager = TokenManager("test-server", config)

    with pytest.raises(TokenAcquisitionError):
        manager.get_token()

    # Should not retry auth errors
    assert len(responses.calls) == 1
