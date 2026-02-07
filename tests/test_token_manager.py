import pytest
import responses
import time
from datetime import datetime, timedelta
from src.token_manager import TokenManager, TokenAcquisitionError


@responses.activate
def test_acquire_token_success():
    """Test successful token acquisition via client credentials flow."""
    responses.add(
        responses.POST,
        "https://login.example.com/oauth2/token",
        json={
            "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
            "token_type": "Bearer",
            "expires_in": 3600
        },
        status=200
    )

    config = {
        "TokenEndpoint": "https://login.example.com/oauth2/token",
        "ClientId": "client123",
        "ClientSecret": "secret456",
        "Scope": "https://dicom.example.com/.default"
    }

    manager = TokenManager("test-server", config)
    token = manager.get_token()

    assert token == "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
    assert len(responses.calls) == 1

    # Verify request was formed correctly
    request = responses.calls[0].request
    assert request.headers["Content-Type"] == "application/x-www-form-urlencoded"
    assert "grant_type=client_credentials" in request.body
    assert "client_id=client123" in request.body
    assert "client_secret=secret456" in request.body
    assert "scope=https%3A%2F%2Fdicom.example.com%2F.default" in request.body


@responses.activate
def test_token_caching():
    """Test that valid tokens are cached and reused."""
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

    # First call should acquire token
    token1 = manager.get_token()
    assert token1 == "token123"
    assert len(responses.calls) == 1

    # Second call should use cached token (no new HTTP request)
    token2 = manager.get_token()
    assert token2 == "token123"
    assert len(responses.calls) == 1  # Still only 1 call


@responses.activate
def test_token_refresh_before_expiry():
    """Test that tokens are refreshed before they expire."""
    # First token expires in 10 seconds
    responses.add(
        responses.POST,
        "https://login.example.com/oauth2/token",
        json={
            "access_token": "token1",
            "token_type": "Bearer",
            "expires_in": 10
        },
        status=200
    )

    # Second token (after refresh)
    responses.add(
        responses.POST,
        "https://login.example.com/oauth2/token",
        json={
            "access_token": "token2",
            "token_type": "Bearer",
            "expires_in": 3600
        },
        status=200
    )

    config = {
        "TokenEndpoint": "https://login.example.com/oauth2/token",
        "ClientId": "client123",
        "ClientSecret": "secret456",
        "Scope": "scope",
        "TokenRefreshBufferSeconds": 300  # 5 minutes buffer
    }

    manager = TokenManager("test-server", config)

    # First call acquires token (expires in 10 seconds)
    token1 = manager.get_token()
    assert token1 == "token1"
    assert len(responses.calls) == 1

    # Token expires in 10 seconds, but we have 300 second buffer
    # So it should be considered expired and refresh immediately
    token2 = manager.get_token()
    assert token2 == "token2"
    assert len(responses.calls) == 2  # New token acquired


@responses.activate
def test_token_acquisition_failure():
    """Test that token acquisition failures raise TokenAcquisitionError."""
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

    with pytest.raises(TokenAcquisitionError, match="Failed to acquire token"):
        manager.get_token()
