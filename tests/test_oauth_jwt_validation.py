"""Tests for OAuth provider JWT validation integration."""
from typing import Any

from src.jwt_validator import JWTValidator
from src.oauth_providers.generic import GenericOAuth2Provider


def test_provider_uses_jwt_validator_when_configured() -> None:
    """Test that provider uses JWT validator when public key configured."""
    config = {
        "TokenEndpoint": "https://example.com/token",
        "ClientId": "test-client",
        "ClientSecret": "test-secret",
        "JWTPublicKey": "-----BEGIN PUBLIC KEY-----\ntest\n-----END PUBLIC KEY-----",
        "JWTAudience": "test-audience",
        "JWTIssuer": "test-issuer",
    }

    provider = GenericOAuth2Provider(config)

    # Verify JWT validator is created
    assert hasattr(provider, "jwt_validator"), "JWT validator should be created"
    assert isinstance(provider.jwt_validator, JWTValidator)
    assert provider.jwt_validator.enabled is True


def test_provider_disables_jwt_validation_when_not_configured() -> None:
    """Test that provider disables JWT validation when no public key."""
    config = {
        "TokenEndpoint": "https://example.com/token",
        "ClientId": "test-client",
        "ClientSecret": "test-secret",
    }

    provider = GenericOAuth2Provider(config)

    # Verify JWT validator is created but disabled
    assert hasattr(provider, "jwt_validator"), "JWT validator should be created"
    assert provider.jwt_validator.enabled is False


def test_validate_token_with_jwt_enabled(mocker: Any) -> None:
    """Test that validate_token uses JWT validator when enabled."""
    config = {
        "TokenEndpoint": "https://example.com/token",
        "ClientId": "test-client",
        "ClientSecret": "test-secret",
        "JWTPublicKey": "-----BEGIN PUBLIC KEY-----\ntest\n-----END PUBLIC KEY-----",
    }

    provider = GenericOAuth2Provider(config)

    # Mock JWT validator
    mock_validator = mocker.patch.object(provider.jwt_validator, "validate")
    mock_validator.return_value = True

    # Call validate_token
    result = provider.validate_token("test.jwt.token")

    # Verify JWT validator was called
    mock_validator.assert_called_once_with("test.jwt.token")
    assert result is True


def test_validate_token_returns_false_on_invalid_jwt(mocker: Any) -> None:
    """Test that validate_token returns False for invalid JWT."""
    config = {
        "TokenEndpoint": "https://example.com/token",
        "ClientId": "test-client",
        "ClientSecret": "test-secret",
        "JWTPublicKey": "-----BEGIN PUBLIC KEY-----\ntest\n-----END PUBLIC KEY-----",
    }

    provider = GenericOAuth2Provider(config)

    # Mock JWT validator to return False
    mock_validator = mocker.patch.object(provider.jwt_validator, "validate")
    mock_validator.return_value = False

    # Call validate_token
    result = provider.validate_token("invalid.jwt.token")

    # Verify result is False
    assert result is False
