"""Tests for Google Cloud Healthcare API OAuth provider."""

from unittest.mock import Mock

import pytest

from src.error_codes import ErrorCode
from src.http_client import HttpClient, HttpResponse
from src.oauth_providers.base import TokenAcquisitionError
from src.oauth_providers.google import GoogleProvider


def test_google_provider_initialization() -> None:
    """Test GoogleProvider initialization."""
    config = {
        "TokenEndpoint": "https://oauth2.googleapis.com/token",
        "ClientId": "test-client-id",
        "ClientSecret": "test-client-secret",
        "Scope": "https://www.googleapis.com/auth/cloud-healthcare",
    }

    provider = GoogleProvider(config)

    assert provider.provider_name == "google"
    assert provider.config.client_id == "test-client-id"
    assert provider.config.token_endpoint == "https://oauth2.googleapis.com/token"


def test_google_provider_detects_invalid_scope() -> None:
    """Test GoogleProvider warns on invalid scope."""
    config = {
        "ClientId": "test-client-id",
        "ClientSecret": "test-client-secret",
        "Scope": "invalid-scope",
        "TokenEndpoint": "https://oauth2.googleapis.com/token",
    }

    # Should initialize but log warning
    provider = GoogleProvider(config)
    assert provider.config.scope == "invalid-scope"


def test_google_provider_sets_default_token_endpoint() -> None:
    """Test GoogleProvider sets default token endpoint if not provided."""
    config = {
        "ClientId": "test-client-id",
        "ClientSecret": "test-client-secret",
        "Scope": "https://www.googleapis.com/auth/cloud-healthcare",
        "TokenEndpoint": "",  # Empty token endpoint
    }

    provider = GoogleProvider(config)
    # Google provider sets default if endpoint is empty
    assert provider.config.token_endpoint == "https://oauth2.googleapis.com/token"


def test_google_provider_acquire_token_success() -> None:
    """Test successful token acquisition."""
    mock_client = Mock(spec=HttpClient)
    mock_client.post.return_value = HttpResponse(
        status_code=200,
        json_data={
            "access_token": "google_test_token",
            "expires_in": 3600,
            "token_type": "Bearer",
        },
    )

    config = {
        "ClientId": "test-client-id",
        "ClientSecret": "test-client-secret",
        "Scope": "https://www.googleapis.com/auth/cloud-healthcare",
        "TokenEndpoint": "https://oauth2.googleapis.com/token",
    }

    provider = GoogleProvider(config, http_client=mock_client)
    token = provider.acquire_token()

    assert token.access_token == "google_test_token"
    assert token.expires_in == 3600
    mock_client.post.assert_called_once()


def test_google_provider_acquire_token_handles_token_acquisition_error() -> None:
    """Test that TokenAcquisitionError is properly logged and re-raised."""
    mock_client = Mock(spec=HttpClient)
    # Simulate an error response that triggers TokenAcquisitionError
    mock_client.post.return_value = HttpResponse(
        status_code=200,
        json_data={"error": "invalid_grant"},  # Missing access_token
    )

    config = {
        "ClientId": "test-client-id",
        "ClientSecret": "test-client-secret",
        "TokenEndpoint": "https://oauth2.googleapis.com/token",
    }

    provider = GoogleProvider(config, http_client=mock_client)

    with pytest.raises(TokenAcquisitionError) as exc_info:
        provider.acquire_token()

    assert exc_info.value.error_code == ErrorCode.TOKEN_INVALID_RESPONSE


def test_google_provider_acquire_token_handles_unexpected_error() -> None:
    """Test that unexpected errors are caught and wrapped."""
    mock_client = Mock(spec=HttpClient)
    # Simulate an unexpected error
    mock_client.post.side_effect = RuntimeError("Unexpected error")

    config = {
        "ClientId": "test-client-id",
        "ClientSecret": "test-client-secret",
        "TokenEndpoint": "https://oauth2.googleapis.com/token",
    }

    provider = GoogleProvider(config, http_client=mock_client)

    with pytest.raises(TokenAcquisitionError) as exc_info:
        provider.acquire_token()

    assert exc_info.value.error_code == ErrorCode.TOKEN_ACQUISITION_FAILED
    assert "Google token acquisition failed" in str(exc_info.value)
