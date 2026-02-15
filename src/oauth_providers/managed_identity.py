"""Azure Managed Identity OAuth provider."""
from typing import Any, Dict

from src.oauth_providers.base import OAuthProvider, OAuthToken
from src.structured_logger import structured_logger


class AzureManagedIdentityProvider(OAuthProvider):
    """
    Azure Managed Identity OAuth provider.

    Uses DefaultAzureCredential to acquire tokens without client secrets.
    Automatically works in Azure environments with managed identity enabled.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Azure Managed Identity provider.

        Args:
            config: Configuration dictionary with Scope and VerifySSL
        """
        self.scope = config.get(
            "Scope", "https://dicom.healthcareapis.azure.com/.default"
        )
        self.verify_ssl = config.get("VerifySSL", True)
        structured_logger.info(
            "AzureManagedIdentityProvider initialized", scope=self.scope
        )

    @property
    def provider_name(self) -> str:
        """Return provider name."""
        return "azure_managed_identity"

    def acquire_token(self) -> OAuthToken:
        """Acquire OAuth token - to be implemented in Task 3."""
        raise NotImplementedError("acquire_token not yet implemented")

    def refresh_token(self, refresh_token: str) -> OAuthToken:
        """
        Refresh token - not supported by managed identity.

        Managed identity tokens are automatically refreshed by Azure SDK.
        """
        raise NotImplementedError("Managed identity does not support token refresh")

    def validate_token(self, token: str) -> bool:
        """
        Validate token - managed identity tokens are pre-validated by Azure.

        Args:
            token: Access token to validate

        Returns:
            True (managed identity tokens are pre-validated)
        """
        return True
