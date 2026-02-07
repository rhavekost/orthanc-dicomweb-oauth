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
