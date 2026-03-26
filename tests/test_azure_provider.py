"""Tests for Azure Active Directory (Entra ID) OAuth provider."""

from unittest.mock import Mock, patch

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


def test_azure_provider_validate_token_disabled_explicitly() -> None:
    """Test that validate_token returns True when DisableJWTValidation is set."""
    config = {
        "TokenEndpoint": (
            "https://login.microsoftonline.com/" "tenant123/oauth2/v2.0/token"
        ),
        "TenantId": "tenant123",
        "ClientId": "client-id",
        "ClientSecret": "client-secret",
        "DisableJWTValidation": True,
    }

    provider = AzureOAuthProvider(config)

    assert provider.validate_token("any_token") is True
    assert provider.validate_token("") is True


def test_azure_provider_validate_token_rejects_invalid_jwt() -> None:
    """Test that validate_token rejects invalid JWT strings."""
    config = {
        "TokenEndpoint": (
            "https://login.microsoftonline.com/" "tenant123/oauth2/v2.0/token"
        ),
        "TenantId": "tenant123",
        "ClientId": "client-id",
        "ClientSecret": "client-secret",
    }

    provider = AzureOAuthProvider(config)

    # Invalid JWT should fail validation (JWKS fetch will fail for invalid token)
    assert provider.validate_token("not_a_valid_jwt") is False


def test_azure_provider_validate_token_with_jwks(
) -> None:
    """Test that validate_token uses JWKS endpoint for validation."""
    import jwt as pyjwt
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives import serialization

    # Generate test RSA key pair
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    public_key = private_key.public_key()

    config = {
        "TokenEndpoint": (
            "https://login.microsoftonline.com/tenant123/oauth2/v2.0/token"
        ),
        "TenantId": "tenant123",
        "ClientId": "client-id",
        "ClientSecret": "client-secret",
        "Scope": "https://dicom.healthcareapis.azure.com/.default",
    }

    provider = AzureOAuthProvider(config)

    # Create a valid JWT signed with our test key
    token = pyjwt.encode(
        {
            "iss": "https://login.microsoftonline.com/tenant123/v2.0",
            "aud": "https://dicom.healthcareapis.azure.com",
            "exp": 9999999999,
            "iat": 1000000000,
        },
        private_key,
        algorithm="RS256",
        headers={"kid": "test-key-id"},
    )

    # Mock PyJWKClient to return our test key
    mock_jwk = Mock()
    mock_jwk.key = public_key

    with patch("src.oauth_providers.azure.pyjwt.PyJWKClient") as mock_client_cls:
        mock_client = Mock()
        mock_client.get_signing_key_from_jwt.return_value = mock_jwk
        mock_client_cls.return_value = mock_client

        result = provider.validate_token(token)

    assert result is True
    mock_client_cls.assert_called_once_with(provider.jwks_uri)


def test_azure_provider_audience_from_scope() -> None:
    """Test audience is derived from scope by stripping /.default."""
    config = {
        "TokenEndpoint": (
            "https://login.microsoftonline.com/tenant123/oauth2/v2.0/token"
        ),
        "TenantId": "tenant123",
        "ClientId": "client-id",
        "ClientSecret": "client-secret",
        "Scope": "https://dicom.healthcareapis.azure.com/.default",
    }

    provider = AzureOAuthProvider(config)
    assert provider._expected_audience == "https://dicom.healthcareapis.azure.com"


def test_azure_provider_common_tenant_logs_warning() -> None:
    """Test that defaulting to 'common' tenant logs a warning."""
    config = {
        "TokenEndpoint": "https://login.microsoftonline.com/common/oauth2/v2.0/token",
        "ClientId": "client-id",
        "ClientSecret": "client-secret",
    }

    with patch("src.oauth_providers.azure.structured_logger") as mock_logger:
        provider = AzureOAuthProvider(config)

    assert provider.tenant_id == "common"
    mock_logger.warning.assert_called()
    warning_msg = mock_logger.warning.call_args[0][0]
    assert "common" in warning_msg
    assert "tenant_id" in warning_msg or "tenant" in warning_msg.lower()


def test_azure_provider_specific_tenant_no_warning() -> None:
    """Test that specific tenant_id does not log a warning."""
    config = {
        "TokenEndpoint": (
            "https://login.microsoftonline.com/my-tenant/oauth2/v2.0/token"
        ),
        "TenantId": "my-tenant",
        "ClientId": "client-id",
        "ClientSecret": "client-secret",
    }

    with patch("src.oauth_providers.azure.structured_logger") as mock_logger:
        provider = AzureOAuthProvider(config)

    assert provider.tenant_id == "my-tenant"
    # Warning should not have been called (info calls from JWT setup are ok)
    mock_logger.warning.assert_not_called()


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
