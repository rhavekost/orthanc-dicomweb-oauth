"""OAuth2 token acquisition and caching for DICOMweb connections."""
import logging
import threading
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import requests

from src.oauth_providers.base import OAuthProvider, TokenAcquisitionError
from src.oauth_providers.factory import OAuthProviderFactory
from src.structured_logger import structured_logger

logger = logging.getLogger(__name__)


class TokenManager:
    """Manages OAuth2 token acquisition, caching, and refresh for a DICOMweb server."""

    def __init__(self, server_name: str, config: Dict[str, Any]):
        """
        Initialize token manager for a DICOMweb server.

        Args:
            server_name: Name of the server (for logging)
            config: Server configuration containing TokenEndpoint, ClientId, etc.
        """
        self.server_name = server_name
        self.config = config
        self._validate_config()

        # Token cache
        self._cached_token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None
        self._lock = threading.Lock()

        # Configuration
        self.token_endpoint = config["TokenEndpoint"]
        self.client_id = config["ClientId"]
        self.client_secret = config["ClientSecret"]
        self.scope = config.get("Scope", "")
        self.refresh_buffer_seconds = config.get("TokenRefreshBufferSeconds", 300)
        self.verify_ssl = config.get("VerifySSL", True)

        # Create OAuth provider
        provider_type = config.get("ProviderType", "auto")
        if provider_type == "auto":
            provider_type = OAuthProviderFactory.auto_detect(config)

        self.provider: OAuthProvider = OAuthProviderFactory.create(
            provider_type=provider_type, config=config
        )

        structured_logger.info(
            "Token manager initialized",
            server=server_name,
            provider=self.provider.provider_name,
        )

    def _validate_config(self) -> None:
        """Validate that required configuration keys are present."""
        required_keys = ["TokenEndpoint", "ClientId", "ClientSecret"]
        missing_keys = [key for key in required_keys if key not in self.config]

        if missing_keys:
            raise ValueError(
                f"Server '{self.server_name}' missing required config keys: "
                f"{missing_keys}"
            )

    def get_token(self) -> str:
        """
        Get a valid OAuth2 access token, acquiring or refreshing as needed.

        Returns:
            Valid access token string

        Raises:
            TokenAcquisitionError: If token acquisition fails
        """
        with self._lock:
            # Check if we have a valid cached token
            if self._is_token_valid():
                structured_logger.debug(
                    "Using cached token",
                    server=self.server_name,
                    operation="get_token",
                    cached=True,
                )
                logger.debug(f"Using cached token for server '{self.server_name}'")
                return self._cached_token

            # Need to acquire a new token
            structured_logger.info(
                "Acquiring new token",
                server=self.server_name,
                operation="get_token",
                cached=False,
            )
            logger.info(f"Acquiring new token for server '{self.server_name}'")
            return self._acquire_token()

    def _is_token_valid(self) -> bool:
        """Check if cached token exists and is not expiring soon."""
        if self._cached_token is None or self._token_expiry is None:
            return False

        # Token is valid if it won't expire within the buffer window
        now = datetime.now(timezone.utc)
        buffer = timedelta(seconds=self.refresh_buffer_seconds)
        return now + buffer < self._token_expiry

    def _acquire_token(self) -> str:
        """
        Acquire a new OAuth2 token using provider with retry logic.

        Returns:
            Access token string

        Raises:
            TokenAcquisitionError: If acquisition fails after all retries
        """
        structured_logger.info(
            "Starting token acquisition",
            server=self.server_name,
            operation="acquire_token",
            provider=self.provider.provider_name,
            endpoint=self.token_endpoint,
        )

        max_retries = 3
        retry_delay = 1  # seconds

        for attempt in range(max_retries):
            try:
                # Use provider to acquire token
                oauth_token = self.provider.acquire_token()

                self._cached_token = oauth_token.access_token
                self._token_expiry = datetime.now(timezone.utc) + timedelta(
                    seconds=oauth_token.expires_in
                )

                # Validate token if provider supports it
                if not self.provider.validate_token(oauth_token.access_token):
                    raise TokenAcquisitionError("Token validation failed")

                structured_logger.info(
                    "Token acquired and validated",
                    server=self.server_name,
                    operation="acquire_token",
                    provider=self.provider.provider_name,
                    expires_in_seconds=oauth_token.expires_in,
                    attempt=attempt + 1,
                )
                logger.info(
                    f"Token acquired for server '{self.server_name}', "
                    f"expires in {oauth_token.expires_in} seconds"
                )

                return self._cached_token

            except (requests.Timeout, requests.ConnectionError) as e:
                if attempt < max_retries - 1:
                    structured_logger.warning(
                        "Token acquisition retry",
                        server=self.server_name,
                        operation="acquire_token",
                        provider=self.provider.provider_name,
                        attempt=attempt + 1,
                        max_attempts=max_retries,
                        error_type=type(e).__name__,
                        error_message=str(e),
                        retry_delay_seconds=retry_delay,
                    )
                    logger.warning(
                        f"Token acquisition attempt {attempt + 1} failed for "
                        f"server '{self.server_name}': {e}. "
                        f"Retrying in {retry_delay}s..."
                    )
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    continue
                else:
                    error_msg = (
                        f"Failed to acquire token for server '{self.server_name}' "
                        f"after {max_retries} attempts: {e}"
                    )
                    structured_logger.error(
                        "Token acquisition failed",
                        server=self.server_name,
                        operation="acquire_token",
                        provider=self.provider.provider_name,
                        error_type=type(e).__name__,
                        error_message=str(e),
                        max_attempts=max_retries,
                    )
                    logger.error(error_msg)
                    raise TokenAcquisitionError(error_msg) from e

            except TokenAcquisitionError:
                # Provider-specific errors, re-raise immediately
                raise

            except Exception as e:
                # Unexpected errors
                error_msg = (
                    f"Failed to acquire token for server '{self.server_name}': {e}"
                )
                structured_logger.error(
                    "Token acquisition failed",
                    server=self.server_name,
                    operation="acquire_token",
                    provider=self.provider.provider_name,
                    error_type=type(e).__name__,
                    error_message=str(e),
                    retryable=False,
                )
                logger.error(error_msg)
                raise TokenAcquisitionError(error_msg) from e

        # This should never be reached, but satisfies mypy
        raise TokenAcquisitionError(
            f"Failed to acquire token for server '{self.server_name}'"
        )
