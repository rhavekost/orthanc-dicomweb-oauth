"""Tests for OAuth provider factory and implementations."""
import pytest
import responses

from src.oauth_providers.azure import AzureOAuthProvider
from src.oauth_providers.base import OAuthConfig
from src.oauth_providers.factory import OAuthProviderFactory
from src.oauth_providers.generic import GenericOAuth2Provider


def test_provider_factory_azure() -> None:
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


def test_provider_factory_generic() -> None:
    """Test creating generic provider."""
    config = {
        "TokenEndpoint": "https://auth.example.com/token",
        "ClientId": "client123",
        "ClientSecret": "secret456",
    }

    provider = OAuthProviderFactory.create("generic", config)

    assert isinstance(provider, GenericOAuth2Provider)
    assert provider.provider_name == "generic-oauth2"


def test_auto_detect_azure() -> None:
    """Test auto-detecting Azure provider."""
    config = {
        "TokenEndpoint": "https://login.microsoftonline.com/tenant/oauth2/v2.0/token",
    }

    provider_type = OAuthProviderFactory.auto_detect(config)
    assert provider_type == "azure"


def test_auto_detect_generic() -> None:
    """Test auto-detecting generic provider."""
    config = {
        "TokenEndpoint": "https://auth.example.com/token",
    }

    provider_type = OAuthProviderFactory.auto_detect(config)
    assert provider_type == "generic"


def test_provider_factory_unknown() -> None:
    """Test error for unknown provider type."""
    config = {
        "TokenEndpoint": "https://auth.example.com/token",
        "ClientId": "client123",
        "ClientSecret": "secret456",
    }

    with pytest.raises(ValueError, match="Unknown provider type"):
        OAuthProviderFactory.create("unknown", config)


@responses.activate  # type: ignore[misc]
def test_generic_provider_acquire_token() -> None:
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


@responses.activate  # type: ignore[misc]
def test_generic_provider_with_scope() -> None:
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


def test_generic_provider_validate_token() -> None:
    """Test generic provider always validates tokens (no JWT validation)."""
    config = OAuthConfig(
        token_endpoint="https://auth.example.com/token",
        client_id="client123",
        client_secret="secret456",
    )

    provider = GenericOAuth2Provider(config)
    # Generic provider doesn't do JWT validation
    assert provider.validate_token("any-token") is True


def test_register_custom_provider() -> None:
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


def test_generic_provider_with_mock_http_client() -> None:
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


def test_generic_provider_refresh_token_success() -> None:
    """Test successful token refresh."""
    from unittest.mock import Mock

    from src.http_client import HttpClient, HttpResponse

    mock_client = Mock(spec=HttpClient)
    mock_client.post.return_value = HttpResponse(
        status_code=200,
        json_data={
            "access_token": "new_token",
            "expires_in": 3600,
            "token_type": "Bearer",
            "refresh_token": "new_refresh_token",
        },
    )

    config = OAuthConfig(
        token_endpoint="https://login.example.com/token",
        client_id="test_client",
        client_secret="test_secret",
    )

    provider = GenericOAuth2Provider(config=config, http_client=mock_client)
    token = provider.refresh_token("old_refresh_token")

    assert token.access_token == "new_token"
    assert token.refresh_token == "new_refresh_token"
    assert token.expires_in == 3600

    # Verify request
    call_args = mock_client.post.call_args
    assert call_args.kwargs["data"]["grant_type"] == "refresh_token"
    assert call_args.kwargs["data"]["refresh_token"] == "old_refresh_token"


def test_generic_provider_refresh_token_missing_access_token() -> None:
    """Test refresh token with invalid response."""
    from unittest.mock import Mock

    from src.error_codes import ErrorCode
    from src.http_client import HttpClient, HttpResponse
    from src.oauth_providers.base import TokenAcquisitionError

    mock_client = Mock(spec=HttpClient)
    mock_client.post.return_value = HttpResponse(
        status_code=200,
        json_data={"error": "invalid_grant"},  # Missing access_token
    )

    config = OAuthConfig(
        token_endpoint="https://login.example.com/token",
        client_id="test_client",
        client_secret="test_secret",
    )

    provider = GenericOAuth2Provider(config=config, http_client=mock_client)

    with pytest.raises(TokenAcquisitionError) as exc_info:
        provider.refresh_token("old_refresh_token")

    assert exc_info.value.error_code == ErrorCode.TOKEN_INVALID_RESPONSE


def test_generic_provider_refresh_token_timeout() -> None:
    """Test refresh token with timeout error."""
    from unittest.mock import Mock

    import requests

    from src.error_codes import ErrorCode, NetworkError
    from src.http_client import HttpClient

    mock_client = Mock(spec=HttpClient)
    mock_client.post.side_effect = requests.Timeout("Connection timeout")

    config = OAuthConfig(
        token_endpoint="https://login.example.com/token",
        client_id="test_client",
        client_secret="test_secret",
    )

    provider = GenericOAuth2Provider(config=config, http_client=mock_client)

    with pytest.raises(NetworkError) as exc_info:
        provider.refresh_token("old_refresh_token")

    assert exc_info.value.error_code == ErrorCode.NETWORK_TIMEOUT


def test_generic_provider_refresh_token_connection_error() -> None:
    """Test refresh token with connection error."""
    from unittest.mock import Mock

    import requests

    from src.error_codes import ErrorCode, NetworkError
    from src.http_client import HttpClient

    mock_client = Mock(spec=HttpClient)
    mock_client.post.side_effect = requests.ConnectionError("Connection failed")

    config = OAuthConfig(
        token_endpoint="https://login.example.com/token",
        client_id="test_client",
        client_secret="test_secret",
    )

    provider = GenericOAuth2Provider(config=config, http_client=mock_client)

    with pytest.raises(NetworkError) as exc_info:
        provider.refresh_token("old_refresh_token")

    assert exc_info.value.error_code == ErrorCode.NETWORK_CONNECTION_ERROR


def test_generic_provider_refresh_token_request_exception() -> None:
    """Test refresh token with general request exception."""
    from unittest.mock import Mock

    import requests

    from src.error_codes import ErrorCode
    from src.http_client import HttpClient
    from src.oauth_providers.base import TokenAcquisitionError

    mock_client = Mock(spec=HttpClient)
    mock_client.post.side_effect = requests.RequestException("Request failed")

    config = OAuthConfig(
        token_endpoint="https://login.example.com/token",
        client_id="test_client",
        client_secret="test_secret",
    )

    provider = GenericOAuth2Provider(config=config, http_client=mock_client)

    with pytest.raises(TokenAcquisitionError) as exc_info:
        provider.refresh_token("old_refresh_token")

    assert exc_info.value.error_code == ErrorCode.TOKEN_REFRESH_FAILED


def test_generic_provider_acquire_token_missing_access_token() -> None:
    """Test acquire token with missing access_token in response."""
    from unittest.mock import Mock

    from src.error_codes import ErrorCode
    from src.http_client import HttpClient, HttpResponse
    from src.oauth_providers.base import TokenAcquisitionError

    mock_client = Mock(spec=HttpClient)
    mock_client.post.return_value = HttpResponse(
        status_code=200,
        json_data={"expires_in": 3600},  # Missing access_token
    )

    config = OAuthConfig(
        token_endpoint="https://login.example.com/token",
        client_id="test_client",
        client_secret="test_secret",
    )

    provider = GenericOAuth2Provider(config=config, http_client=mock_client)

    with pytest.raises(TokenAcquisitionError) as exc_info:
        provider.acquire_token()

    assert exc_info.value.error_code == ErrorCode.TOKEN_INVALID_RESPONSE
    assert "missing access_token" in str(exc_info.value)


def test_generic_provider_with_jwt_validation() -> None:
    """Test generic provider with JWT validation enabled."""
    config = {
        "TokenEndpoint": "https://login.example.com/token",
        "ClientId": "test_client",
        "ClientSecret": "test_secret",
        "JWTPublicKey": (
            "-----BEGIN PUBLIC KEY-----\n" "MIIBIjANBg...\n" "-----END PUBLIC KEY-----"
        ),
        "JWTAudience": "api://test_client",
        "JWTIssuer": "https://login.example.com",
        "JWTAlgorithms": ["RS256"],
    }

    provider = GenericOAuth2Provider(config)

    assert provider.jwt_validator.enabled is True
    assert provider.jwt_validator.expected_audience == "api://test_client"
    assert provider.jwt_validator.expected_issuer == "https://login.example.com"


def test_generic_provider_with_jwt_validation_string_algorithm() -> None:
    """Test generic provider with JWT validation using string algorithm."""
    config = {
        "TokenEndpoint": "https://login.example.com/token",
        "ClientId": "test_client",
        "ClientSecret": "test_secret",
        "JWTPublicKey": (
            "-----BEGIN PUBLIC KEY-----\n" "MIIBIjANBg...\n" "-----END PUBLIC KEY-----"
        ),
        "JWTAudience": "api://test_client",
        "JWTIssuer": "https://login.example.com",
        "JWTAlgorithms": "RS256",  # String instead of list
    }

    provider = GenericOAuth2Provider(config)

    assert provider.jwt_validator.enabled is True


def test_generic_provider_with_partial_jwt_config() -> None:
    """Test generic provider with partial JWT config (no public key)."""
    config = {
        "TokenEndpoint": "https://login.example.com/token",
        "ClientId": "test_client",
        "ClientSecret": "test_secret",
        "JWTAudience": "api://test_client",
        "JWTIssuer": "https://login.example.com",
    }

    provider = GenericOAuth2Provider(config)

    # JWT validator should exist but not be enabled (no public key)
    assert provider.jwt_validator.enabled is False


def test_generic_provider_refresh_token_keeps_old_refresh_token() -> None:
    """Test refresh token keeps old refresh token if new one not provided."""
    from unittest.mock import Mock

    from src.http_client import HttpClient, HttpResponse

    mock_client = Mock(spec=HttpClient)
    mock_client.post.return_value = HttpResponse(
        status_code=200,
        json_data={
            "access_token": "new_token",
            "expires_in": 3600,
            "token_type": "Bearer",
            # No new refresh_token in response
        },
    )

    config = OAuthConfig(
        token_endpoint="https://login.example.com/token",
        client_id="test_client",
        client_secret="test_secret",
    )

    provider = GenericOAuth2Provider(config=config, http_client=mock_client)
    token = provider.refresh_token("old_refresh_token")

    # Should keep old refresh token
    assert token.refresh_token == "old_refresh_token"


def test_generic_provider_acquire_token_with_default_values() -> None:
    """Test acquire token uses default values for optional fields."""
    from unittest.mock import Mock

    from src.http_client import HttpClient, HttpResponse

    mock_client = Mock(spec=HttpClient)
    mock_client.post.return_value = HttpResponse(
        status_code=200,
        json_data={
            "access_token": "token123",
            # No expires_in, token_type, refresh_token, or scope
        },
    )

    config = OAuthConfig(
        token_endpoint="https://login.example.com/token",
        client_id="test_client",
        client_secret="test_secret",
    )

    provider = GenericOAuth2Provider(config=config, http_client=mock_client)
    token = provider.acquire_token()

    # Should use default values
    assert token.access_token == "token123"
    assert token.expires_in == 3600  # Default
    assert token.token_type == "Bearer"  # Default
    assert token.refresh_token is None
    assert token.scope is None


def test_provider_factory_managed_identity() -> None:
    """Test factory creates managed identity provider."""
    from src.oauth_providers.managed_identity import AzureManagedIdentityProvider

    config = {
        "Type": "AzureManagedIdentity",
        "Scope": "https://dicom.healthcareapis.azure.com/.default",
    }

    provider = OAuthProviderFactory.create("azuremanagedidentity", config)

    assert isinstance(provider, AzureManagedIdentityProvider)
    assert provider.scope == "https://dicom.healthcareapis.azure.com/.default"
