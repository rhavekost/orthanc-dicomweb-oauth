"""Tests for Azure Active Directory (Entra ID) OAuth provider."""

from unittest.mock import Mock

from src.http_client import HttpClient, HttpResponse
from src.oauth_providers.azure import AzureOAuthProvider
from src.oauth_providers.base import OAuthConfig


def test_azure_provider_initialization_with_dict_config() -> None:
    """Test AzureOAuthProvider initialization with dict config."""
    config = {
        "TokenEndpoint": (
            "https://login.microsoftonline.com/" "tenant123/oauth2/v2.0/token"
        ),
        "TenantId": "tenant123",
        "ClientId": "client-id",
        "ClientSecret": "client-secret",
        "Scope": "https://dicom.healthcareapis.azure.com/.default",
    }

    provider = AzureOAuthProvider(config)

    assert provider.provider_name == "azure-ad"
    assert provider.tenant_id == "tenant123"
    assert provider.config.client_id == "client-id"
    assert provider.jwks_uri == (
        "https://login.microsoftonline.com/" "tenant123/discovery/v2.0/keys"
    )
    assert provider.issuer == ("https://login.microsoftonline.com/tenant123/v2.0")


def test_azure_provider_initialization_with_tenant_id_param() -> None:
    """Test AzureOAuthProvider initialization with explicit tenant_id."""
    config = {
        "TokenEndpoint": (
            "https://login.microsoftonline.com/" "tenant456/oauth2/v2.0/token"
        ),
        "ClientId": "client-id",
        "ClientSecret": "client-secret",
        "Scope": "https://dicom.healthcareapis.azure.com/.default",
    }

    provider = AzureOAuthProvider(config, tenant_id="tenant456")

    assert provider.tenant_id == "tenant456"


def test_azure_provider_defaults_to_common_tenant() -> None:
    """Test AzureOAuthProvider defaults to 'common' tenant."""
    config = {
        "TokenEndpoint": ("https://login.microsoftonline.com/common/oauth2/v2.0/token"),
        "ClientId": "client-id",
        "ClientSecret": "client-secret",
    }

    provider = AzureOAuthProvider(config)

    assert provider.tenant_id == "common"


def test_azure_provider_with_jwt_config() -> None:
    """Test AzureOAuthProvider with JWT validation configured."""
    config = {
        "TokenEndpoint": (
            "https://login.microsoftonline.com/" "tenant123/oauth2/v2.0/token"
        ),
        "TenantId": "tenant123",
        "ClientId": "client-id",
        "ClientSecret": "client-secret",
        "JWTPublicKey": (
            "-----BEGIN PUBLIC KEY-----\n" "MIIBIjANBg...\n" "-----END PUBLIC KEY-----"
        ),
        "JWTAudience": "api://client-id",
        "JWTIssuer": ("https://login.microsoftonline.com/tenant123/v2.0"),
    }

    provider = AzureOAuthProvider(config)

    assert provider.jwt_validator is not None
    assert provider.jwt_validator.enabled is True


def test_azure_provider_without_jwt_config() -> None:
    """Test AzureOAuthProvider without JWT validation."""
    config = {
        "TokenEndpoint": (
            "https://login.microsoftonline.com/" "tenant123/oauth2/v2.0/token"
        ),
        "TenantId": "tenant123",
        "ClientId": "client-id",
        "ClientSecret": "client-secret",
    }

    provider = AzureOAuthProvider(config)

    assert provider.jwt_validator is not None
    assert provider.jwt_validator.enabled is False


def test_azure_provider_initialization_with_oauth_config() -> None:
    """Test AzureOAuthProvider initialization with OAuthConfig object."""
    oauth_config = OAuthConfig(
        token_endpoint=(
            "https://login.microsoftonline.com/" "tenant123/oauth2/v2.0/token"
        ),
        client_id="client-id",
        client_secret="client-secret",
        scope="https://dicom.healthcareapis.azure.com/.default",
    )

    provider = AzureOAuthProvider(oauth_config, tenant_id="tenant123")

    assert provider.provider_name == "azure-ad"
    assert provider.tenant_id == "tenant123"
    assert provider.jwt_validator.enabled is False


def test_azure_provider_validate_token_always_returns_true() -> None:
    """Test that validate_token returns True (validation disabled)."""
    config = {
        "TokenEndpoint": (
            "https://login.microsoftonline.com/" "tenant123/oauth2/v2.0/token"
        ),
        "TenantId": "tenant123",
        "ClientId": "client-id",
        "ClientSecret": "client-secret",
    }

    provider = AzureOAuthProvider(config)

    # TODO: This should be fixed to properly validate tokens
    # For now, it always returns True
    assert provider.validate_token("any_token") is True
    assert provider.validate_token("") is True


def test_azure_provider_inherits_generic_acquire_token() -> None:
    """Test AzureOAuthProvider inherits token acquisition."""
    mock_client = Mock(spec=HttpClient)
    mock_client.post.return_value = HttpResponse(
        status_code=200,
        json_data={
            "access_token": "azure_test_token",
            "expires_in": 3600,
            "token_type": "Bearer",
        },
    )

    config = {
        "TokenEndpoint": (
            "https://login.microsoftonline.com/" "tenant123/oauth2/v2.0/token"
        ),
        "TenantId": "tenant123",
        "ClientId": "client-id",
        "ClientSecret": "client-secret",
    }

    provider = AzureOAuthProvider(config, http_client=mock_client)
    token = provider.acquire_token()

    assert token.access_token == "azure_test_token"
    assert token.expires_in == 3600
    mock_client.post.assert_called_once()
