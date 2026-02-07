"""Tests for Google Cloud Healthcare API OAuth provider."""

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
