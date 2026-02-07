"""Tests for secrets encryption in memory."""
import pytest

from src.secrets_manager import SecretsManager


def test_encrypt_decrypt_secret() -> None:
    """Test that secrets can be encrypted and decrypted."""
    manager = SecretsManager()
    original_secret = "my-secret-value"

    encrypted = manager.encrypt_secret(original_secret)
    assert encrypted != original_secret.encode("utf-8"), "Secret should be encrypted"

    decrypted = manager.decrypt_secret(encrypted)
    assert decrypted == original_secret, "Decrypted secret should match original"


def test_encrypted_secret_is_bytes() -> None:
    """Test that encrypted secrets are stored as bytes."""
    manager = SecretsManager()
    encrypted = manager.encrypt_secret("test-secret")
    assert isinstance(encrypted, bytes), "Encrypted secret should be bytes"


def test_different_instances_use_different_keys() -> None:
    """Test that different instances generate different keys."""
    manager1 = SecretsManager()
    manager2 = SecretsManager()

    secret = "test-secret"
    encrypted1 = manager1.encrypt_secret(secret)
    encrypted2 = manager2.encrypt_secret(secret)

    assert (
        encrypted1 != encrypted2
    ), "Different instances should produce different ciphertexts"


def test_decrypt_wrong_key_raises_error() -> None:
    """Test that decrypting with wrong key raises error."""
    manager1 = SecretsManager()
    manager2 = SecretsManager()

    encrypted = manager1.encrypt_secret("test-secret")

    with pytest.raises(Exception):  # cryptography.fernet.InvalidToken
        manager2.decrypt_secret(encrypted)
