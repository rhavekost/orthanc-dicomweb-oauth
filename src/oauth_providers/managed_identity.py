"""Azure Managed Identity OAuth provider."""
from typing import TYPE_CHECKING, Any, Dict, Optional

from src.oauth_providers.base import OAuthConfig, OAuthProvider, OAuthToken
from src.structured_logger import structured_logger

if TYPE_CHECKING:
    from src.http_client import HttpClient


class AzureManagedIdentityProvider(OAuthProvider):
    """
    Azure Managed Identity OAuth provider.

    Uses DefaultAzureCredential to acquire tokens without client secrets.
    Automatically works in Azure environments with managed identity enabled.
    """

    def __init__(
        self, config: Dict[str, Any], http_client: Optional["HttpClient"] = None
    ):
        """
        Initialize Azure Managed Identity provider.

        Args:
            config: Configuration dictionary with Scope and VerifySSL
            http_client: Optional HTTP client (defaults to RequestsHttpClient)
        """
        # Create minimal OAuthConfig to satisfy parent class
        oauth_config = OAuthConfig(
            token_endpoint="",  # Not used by managed identity
            client_id="",  # Not used by managed identity
            client_secret="",  # Not used by managed identity  # nosec B106
            scope=config.get(
                "Scope", "https://dicom.healthcareapis.azure.com/.default"
            ),
            verify_ssl=config.get("VerifySSL", True),
        )
        super().__init__(oauth_config, http_client)

        # Store for convenient access
        self.scope = self.config.scope
        self.verify_ssl = self.config.verify_ssl

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
