"""Tests for Azure Active Directory (Entra ID) OAuth provider."""

from unittest.mock import Mock, patch

import pytest

from src.http_client import HttpClient, HttpResponse
from src.oauth_providers.azure import AzureOAuthProvider
from src.oauth_providers.base import OAuthConfig


@pytest.fixture(autouse=True)
def mock_jwks_client():
    """Prevent real network calls to Azure JWKS endpoint in all tests.

    AzureOAuthProvider.__init__ now caches a PyJWKClient instance. Without
    this fixture every test that constructs a provider would make a live
    network request to login.microsoftonline.com.

    Tests that need to control key-lookup behaviour (e.g. validate_token
    tests) should patch PyJWKClient themselves inside a narrower context and
    the autouse patch will be superseded for that scope.
    """
    with patch("src.oauth_providers.azure._PyJWKClient"):
        yield


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


def test_azure_provider_validate_token_with_jwks() -> None:
    """Test that validate_token uses JWKS endpoint for validation."""
    import jwt as pyjwt
    from cryptography.hazmat.primitives.asymmetric import rsa

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

    # Mock PyJWKClient at construction time so _jwks_client is the mock instance.
    # The client is cached on the provider, so validate_token reuses it without
    # making a new network call.
    mock_jwk = Mock()
    mock_jwk.key = public_key

    with patch("src.oauth_providers.azure._PyJWKClient") as mock_client_cls:
        mock_client = Mock()
        mock_client.get_signing_key_from_jwt.return_value = mock_jwk
        mock_client_cls.return_value = mock_client

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

        result = provider.validate_token(token)

    assert result is True
    # PyJWKClient constructed once (at __init__), not on every validate_token call
    mock_client_cls.assert_called_once_with(provider.jwks_uri)
    mock_client.get_signing_key_from_jwt.assert_called_once_with(token)


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
    """Test that defaulting to 'common' tenant logs a tenant warning.

    Two warnings are expected: one for the common tenant and one for
    missing audience verification (no /.default scope in this config).
    """
    config = {
        "TokenEndpoint": "https://login.microsoftonline.com/common/oauth2/v2.0/token",
        "ClientId": "client-id",
        "ClientSecret": "client-secret",
    }

    with patch("src.oauth_providers.azure.structured_logger") as mock_logger:
        provider = AzureOAuthProvider(config)

    assert provider.tenant_id == "common"
    all_warning_msgs = [call[0][0] for call in mock_logger.warning.call_args_list]
    assert any(
        "common" in msg for msg in all_warning_msgs
    ), "Expected a warning about the 'common' tenant"


def test_azure_provider_specific_tenant_no_warning_with_default_scope() -> None:
    """Test that a specific tenant with a /.default scope logs no warnings."""
    config = {
        "TokenEndpoint": (
            "https://login.microsoftonline.com/my-tenant/oauth2/v2.0/token"
        ),
        "TenantId": "my-tenant",
        "ClientId": "client-id",
        "ClientSecret": "client-secret",
        "Scope": "https://dicom.healthcareapis.azure.com/.default",
    }

    with patch("src.oauth_providers.azure.structured_logger") as mock_logger:
        provider = AzureOAuthProvider(config)

    assert provider.tenant_id == "my-tenant"
    mock_logger.warning.assert_not_called()


def test_azure_provider_specific_tenant_warns_when_no_default_scope() -> None:
    """Test that a specific tenant without /.default scope warns about audience."""
    config = {
        "TokenEndpoint": (
            "https://login.microsoftonline.com/my-tenant/oauth2/v2.0/token"
        ),
        "TenantId": "my-tenant",
        "ClientId": "client-id",
        "ClientSecret": "client-secret",
        # No Scope — audience verification will be skipped
    }

    with patch("src.oauth_providers.azure.structured_logger") as mock_logger:
        provider = AzureOAuthProvider(config)

    assert provider.tenant_id == "my-tenant"
    all_warning_msgs = [call[0][0] for call in mock_logger.warning.call_args_list]
    assert any(
        "audience" in msg.lower() for msg in all_warning_msgs
    ), "Expected a warning about disabled audience verification"


def test_azure_provider_common_tenant_skips_issuer_verification() -> None:
    """Test that common tenant disables issuer verification.

    Azure tokens issued via the 'common' endpoint carry the real tenant GUID
    in the 'iss' claim, not the literal string 'common'. Verifying against
    a static issuer of 'common' would always fail, so _verify_issuer must
    be False when tenant_id == 'common'.
    """
    config = {
        "TokenEndpoint": "https://login.microsoftonline.com/common/oauth2/v2.0/token",
        "ClientId": "client-id",
        "ClientSecret": "client-secret",
    }

    with patch("src.oauth_providers.azure._PyJWKClient"):
        provider = AzureOAuthProvider(config)

    assert provider.tenant_id == "common"
    assert provider._verify_issuer is False


def test_azure_provider_specific_tenant_enables_issuer_verification() -> None:
    """Test that a specific tenant enables issuer verification."""
    config = {
        "TokenEndpoint": (
            "https://login.microsoftonline.com/tenant123/oauth2/v2.0/token"
        ),
        "TenantId": "tenant123",
        "ClientId": "client-id",
        "ClientSecret": "client-secret",
    }

    with patch("src.oauth_providers.azure._PyJWKClient"):
        provider = AzureOAuthProvider(config)

    assert provider._verify_issuer is True


def test_azure_provider_jwks_client_reused_across_validate_calls() -> None:
    """Test that PyJWKClient is constructed once and reused, not per-call."""
    import jwt as pyjwt
    from cryptography.hazmat.primitives.asymmetric import rsa

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
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

    mock_jwk = Mock()
    mock_jwk.key = public_key

    with patch("src.oauth_providers.azure._PyJWKClient") as mock_client_cls:
        mock_client = Mock()
        mock_client.get_signing_key_from_jwt.return_value = mock_jwk
        mock_client_cls.return_value = mock_client

        provider = AzureOAuthProvider(config)

        token = pyjwt.encode(
            {
                "iss": "https://login.microsoftonline.com/tenant123/v2.0",
                "aud": "https://dicom.healthcareapis.azure.com",
                "exp": 9999999999,
                "iat": 1000000000,
            },
            private_key,
            algorithm="RS256",
        )

        provider.validate_token(token)
        provider.validate_token(token)

    # PyJWKClient should be constructed exactly once (in __init__), regardless
    # of how many times validate_token is called.
    assert mock_client_cls.call_count == 1
    assert mock_client.get_signing_key_from_jwt.call_count == 2


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
