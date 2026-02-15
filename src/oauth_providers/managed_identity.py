"""Azure Managed Identity OAuth provider."""
import time
from typing import TYPE_CHECKING, Any, Dict, Optional

from azure.core.exceptions import ClientAuthenticationError
from azure.identity import DefaultAzureCredential

from src.error_codes import ErrorCode, TokenAcquisitionError
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
        self._credential: Optional[DefaultAzureCredential] = None

        structured_logger.info(
            "AzureManagedIdentityProvider initialized", scope=self.scope
        )

    @property
    def provider_name(self) -> str:
        """Return provider name."""
        return "azure_managed_identity"

    @property
    def credential(self) -> DefaultAzureCredential:
        """Lazy-load DefaultAzureCredential."""
        if self._credential is None:
            self._credential = DefaultAzureCredential()
        return self._credential

    def acquire_token(self) -> OAuthToken:
        """
        Acquire OAuth token using managed identity.

        Returns:
            OAuthToken with access token and expiry

        Raises:
            TokenAcquisitionError: If token acquisition fails
        """
        try:
            structured_logger.debug(
                "Acquiring token via managed identity", scope=self.scope
            )

            token = self.credential.get_token(self.scope)

            if token and token.token:
                structured_logger.info(
                    "Token acquired successfully via managed identity"
                )
                # Azure SDK returns AccessToken with token and expires_on
                # Calculate expires_in from expires_on timestamp
                expires_in = max(0, int(token.expires_on - time.time()))

                return OAuthToken(
                    access_token=token.token,
                    expires_in=expires_in,
                    token_type="Bearer",  # nosec B106
                )

            raise TokenAcquisitionError(
                error_code=ErrorCode.TOKEN_ACQUISITION_FAILED,
                message="Managed identity returned empty token",
            )

        except ClientAuthenticationError as e:
            structured_logger.error(
                "Managed identity authentication failed", error=str(e)
            )
            raise TokenAcquisitionError(
                error_code=ErrorCode.TOKEN_ACQUISITION_FAILED,
                message=f"Managed identity authentication failed: {e}",
            ) from e
        except TokenAcquisitionError:
            # Re-raise our own errors
            raise
        except Exception as e:
            structured_logger.error("Unexpected error acquiring token", error=str(e))
            raise TokenAcquisitionError(
                error_code=ErrorCode.TOKEN_ACQUISITION_FAILED,
                message=f"Token acquisition error: {e}",
            ) from e

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
