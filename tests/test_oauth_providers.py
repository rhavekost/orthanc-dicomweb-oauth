"""Tests for OAuth provider factory and implementations."""
import pytest
import responses

from src.oauth_providers.azure import AzureOAuthProvider
from src.oauth_providers.base import OAuthConfig
from src.oauth_providers.factory import OAuthProviderFactory
from src.oauth_providers.generic import GenericOAuth2Provider


def test_provider_factory_azure():
    """Test creating Azure provider."""
    config = {
        "TokenEndpoint": "https://login.microsoftonline.com/tenant/oauth2/v2.0/token",
        "TenantId": "test-tenant",
        "ClientId": "client123",
        "ClientSecret": "secret456",
        "Scope": "https://dicom.healthcareapis.azure.com/.default",
    }

    provider = OAuthProviderFactory.create("azure", config)

    assert isinstance(provider, AzureOAuthProvider)
    assert provider.provider_name == "azure-ad"
    assert provider.tenant_id == "test-tenant"


def test_provider_factory_generic():
    """Test creating generic provider."""
    config = {
        "TokenEndpoint": "https://auth.example.com/token",
        "ClientId": "client123",
        "ClientSecret": "secret456",
    }

    provider = OAuthProviderFactory.create("generic", config)

    assert isinstance(provider, GenericOAuth2Provider)
    assert provider.provider_name == "generic-oauth2"


def test_auto_detect_azure():
    """Test auto-detecting Azure provider."""
    config = {
        "TokenEndpoint": "https://login.microsoftonline.com/tenant/oauth2/v2.0/token",
    }

    provider_type = OAuthProviderFactory.auto_detect(config)
    assert provider_type == "azure"


def test_auto_detect_generic():
    """Test auto-detecting generic provider."""
    config = {
        "TokenEndpoint": "https://auth.example.com/token",
    }

    provider_type = OAuthProviderFactory.auto_detect(config)
    assert provider_type == "generic"


def test_provider_factory_unknown():
    """Test error for unknown provider type."""
    config = {
        "TokenEndpoint": "https://auth.example.com/token",
        "ClientId": "client123",
        "ClientSecret": "secret456",
    }

    with pytest.raises(ValueError, match="Unknown provider type"):
        OAuthProviderFactory.create("unknown", config)


@responses.activate
def test_generic_provider_acquire_token():
    """Test generic provider token acquisition."""
    responses.add(
        responses.POST,
        "https://auth.example.com/token",
        json={"access_token": "token123", "token_type": "Bearer", "expires_in": 3600},
        status=200,
    )

    config = OAuthConfig(
        token_endpoint="https://auth.example.com/token",
        client_id="client123",
        client_secret="secret456",
        scope="read write",
    )

    provider = GenericOAuth2Provider(config)
    token = provider.acquire_token()

    assert token.access_token == "token123"
    assert token.expires_in == 3600
    assert token.token_type == "Bearer"


@responses.activate
def test_generic_provider_with_scope():
    """Test generic provider includes scope in request."""
    responses.add(
        responses.POST,
        "https://auth.example.com/token",
        json={"access_token": "token123", "expires_in": 3600},
        status=200,
    )

    config = OAuthConfig(
        token_endpoint="https://auth.example.com/token",
        client_id="client123",
        client_secret="secret456",
        scope="custom.scope",
    )

    provider = GenericOAuth2Provider(config)
    provider.acquire_token()

    # Check that scope was included in request
    assert len(responses.calls) == 1
    request_body = responses.calls[0].request.body
    assert "scope=custom.scope" in request_body


def test_generic_provider_validate_token():
    """Test generic provider always validates tokens (no JWT validation)."""
    config = OAuthConfig(
        token_endpoint="https://auth.example.com/token",
        client_id="client123",
        client_secret="secret456",
    )

    provider = GenericOAuth2Provider(config)
    # Generic provider doesn't do JWT validation
    assert provider.validate_token("any-token") is True


def test_register_custom_provider():
    """Test registering a custom provider type."""

    class CustomProvider(GenericOAuth2Provider):
        @property
        def provider_name(self) -> str:
            return "custom"

    OAuthProviderFactory.register_provider("custom", CustomProvider)

    config = {
        "TokenEndpoint": "https://custom.example.com/token",
        "ClientId": "client123",
        "ClientSecret": "secret456",
    }

    provider = OAuthProviderFactory.create("custom", config)
    assert isinstance(provider, CustomProvider)
    assert provider.provider_name == "custom"


def test_generic_provider_with_mock_http_client():
    """Test provider with injected mock HTTP client."""
    from unittest.mock import Mock

    from src.http_client import HttpClient, HttpResponse

    # Create mock HTTP client
    mock_client = Mock(spec=HttpClient)
    mock_client.post.return_value = HttpResponse(
        status_code=200,
        json_data={
            "access_token": "test_token",
            "expires_in": 3600,
            "token_type": "Bearer",
        },
    )

    # Create provider with mock client
    config = OAuthConfig(
        token_endpoint="https://login.example.com/token",
        client_id="test_client",
        client_secret="test_secret",
        scope="api",
    )

    provider = GenericOAuth2Provider(config=config, http_client=mock_client)

    # Acquire token
    token = provider.acquire_token()

    # Verify mock was called correctly
    mock_client.post.assert_called_once()
    call_args = mock_client.post.call_args

    assert call_args.kwargs["url"] == "https://login.example.com/token"
    assert "grant_type" in call_args.kwargs["data"]
    assert call_args.kwargs["data"]["grant_type"] == "client_credentials"

    # Verify token returned
    assert token.access_token == "test_token"
    assert token.expires_in == 3600
