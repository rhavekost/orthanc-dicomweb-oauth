"""Base OAuth provider interface."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from src.error_codes import TokenAcquisitionError

if TYPE_CHECKING:
    from src.http_client import HttpClient

# Re-export for backwards compatibility
__all__ = ["TokenAcquisitionError", "OAuthToken", "OAuthConfig", "OAuthProvider"]


@dataclass
class OAuthToken:
    """OAuth token response."""

    access_token: str
    expires_in: int
    token_type: str = "Bearer"
    refresh_token: Optional[str] = None
    scope: Optional[str] = None


@dataclass
class OAuthConfig:
    """OAuth provider configuration."""

    token_endpoint: str
    client_id: str
    client_secret: str
    scope: str = ""
    verify_ssl: bool = True


class OAuthProvider(ABC):
    """
    Abstract base class for OAuth providers.

    Implementations must provide token acquisition logic
    specific to each OAuth provider (Azure, Google, Keycloak, etc.).
    """

    def __init__(self, config: OAuthConfig, http_client: Optional["HttpClient"] = None):
        """
        Initialize OAuth provider.

        Args:
            config: OAuth configuration
            http_client: Optional HTTP client (defaults to RequestsHttpClient)
        """
        self.config = config
        self._http_client = http_client

    @property
    def http_client(self) -> "HttpClient":
        """Get HTTP client, creating default if needed."""
        if self._http_client is None:
            from src.http_client import RequestsHttpClient

            self._http_client = RequestsHttpClient()
        return self._http_client

    @abstractmethod
    def acquire_token(self) -> OAuthToken:
        """
        Acquire an OAuth token from the provider.

        Returns:
            OAuthToken with access token and expiry

        Raises:
            TokenAcquisitionError: If acquisition fails
        """
        pass

    def validate_token(self, token: str) -> bool:
        """
        Validate access token.

        Base implementation performs JWT signature validation if configured.
        Subclasses can override to add provider-specific validation.

        Args:
            token: Access token to validate

        Returns:
            True if token is valid, False otherwise
        """
        # Check if JWT validator is configured
        if hasattr(self, "jwt_validator") and self.jwt_validator.enabled:
            result: bool = self.jwt_validator.validate(token)
            return result

        # No validation configured, assume valid
        return True

    @abstractmethod
    def refresh_token(self, refresh_token: str) -> OAuthToken:
        """
        Refresh an access token using a refresh token.

        Args:
            refresh_token: Refresh token

        Returns:
            New OAuthToken

        Raises:
            TokenAcquisitionError: If refresh fails
        """
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name (e.g., 'azure', 'google')."""
        pass
