"""Tests for TokenManager secrets encryption."""
from src.token_manager import TokenManager


def test_token_manager_encrypts_client_secret() -> None:
    """Test that TokenManager encrypts client secret in memory."""
    config = {
        "TokenEndpoint": "https://example.com/token",
        "ClientId": "test-client-id",
        "ClientSecret": "plaintext-secret",
        "ProviderType": "generic",
    }

    manager = TokenManager("test-server", config)

    # Verify client_secret attribute doesn't exist (encrypted instead)
    assert not hasattr(
        manager, "client_secret"
    ), "client_secret should not be stored in plaintext"

    # Verify encrypted secret exists
    assert hasattr(
        manager, "_encrypted_client_secret"
    ), "Encrypted client secret should be stored"

    # Verify it's bytes
    assert isinstance(
        manager._encrypted_client_secret, bytes
    ), "Encrypted secret should be bytes"


def test_token_manager_can_decrypt_client_secret() -> None:
    """Test that TokenManager can decrypt client secret when needed."""
    config = {
        "TokenEndpoint": "https://example.com/token",
        "ClientId": "test-client-id",
        "ClientSecret": "my-secret-value",
        "ProviderType": "generic",
    }

    manager = TokenManager("test-server", config)

    # Use private method to get decrypted secret
    decrypted = manager._get_client_secret()
    assert decrypted == "my-secret-value", "Decrypted secret should match original"


def test_cached_token_is_encrypted() -> None:
    """Test that cached tokens are encrypted in memory."""
    config = {
        "TokenEndpoint": "https://example.com/token",
        "ClientId": "test-client-id",
        "ClientSecret": "test-secret",
        "ProviderType": "generic",
    }

    manager = TokenManager("test-server", config)

    # Manually set a cached token (simulating token acquisition)
    manager._set_cached_token("eyJ0eXAiOiJKV1QiLCJhbGc")

    # Verify _cached_token doesn't exist in plaintext
    assert (
        not hasattr(manager, "_cached_token") or manager._cached_token is None
    ), "Token should not be stored in plaintext"

    # Verify encrypted token exists
    assert hasattr(
        manager, "_encrypted_cached_token"
    ), "Encrypted token should be stored"
