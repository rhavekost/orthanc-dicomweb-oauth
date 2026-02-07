"""Secrets encryption manager for protecting sensitive data in memory."""
from cryptography.fernet import Fernet


class SecretsManager:
    """
    Manages encryption/decryption of secrets in memory.

    Each instance generates its own encryption key, ensuring that
    secrets are encrypted uniquely per TokenManager instance.

    Example:
        >>> manager = SecretsManager()
        >>> encrypted = manager.encrypt_secret("my-secret")
        >>> decrypted = manager.decrypt_secret(encrypted)
        >>> assert decrypted == "my-secret"
    """

    def __init__(self) -> None:
        """Initialize with a new encryption key."""
        self._key = Fernet.generate_key()
        self._cipher = Fernet(self._key)

    def encrypt_secret(self, secret: str) -> bytes:
        """
        Encrypt a secret string.

        Args:
            secret: The plaintext secret to encrypt

        Returns:
            Encrypted secret as bytes
        """
        encrypted: bytes = self._cipher.encrypt(secret.encode("utf-8"))
        return encrypted

    def decrypt_secret(self, encrypted_secret: bytes) -> str:
        """
        Decrypt an encrypted secret.

        Args:
            encrypted_secret: The encrypted secret bytes

        Returns:
            Decrypted plaintext secret

        Raises:
            cryptography.fernet.InvalidToken: If decryption fails
        """
        decrypted_bytes: bytes = self._cipher.decrypt(encrypted_secret)
        return decrypted_bytes.decode("utf-8")
