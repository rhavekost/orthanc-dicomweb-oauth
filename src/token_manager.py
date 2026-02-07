"""OAuth2 token acquisition and caching for DICOMweb connections."""
import logging
import time
import threading
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional
import requests


logger = logging.getLogger(__name__)


class TokenAcquisitionError(Exception):
    """Raised when token acquisition fails."""
    pass


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

    def _validate_config(self) -> None:
        """Validate that required configuration keys are present."""
        required_keys = ["TokenEndpoint", "ClientId", "ClientSecret"]
        missing_keys = [key for key in required_keys if key not in self.config]

        if missing_keys:
            raise ValueError(
                f"Server '{self.server_name}' missing required config keys: {missing_keys}"
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
                logger.debug(f"Using cached token for server '{self.server_name}'")
                return self._cached_token

            # Need to acquire a new token
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
        Acquire a new OAuth2 token via client credentials flow.

        Returns:
            Access token string

        Raises:
            TokenAcquisitionError: If acquisition fails
        """
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        if self.scope:
            data["scope"] = self.scope

        try:
            response = requests.post(
                self.token_endpoint,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=30
            )
            response.raise_for_status()

            token_data = response.json()
            self._cached_token = token_data["access_token"]
            expires_in = token_data.get("expires_in", 3600)
            self._token_expiry = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

            logger.info(
                f"Token acquired for server '{self.server_name}', "
                f"expires in {expires_in} seconds"
            )

            return self._cached_token

        except requests.RequestException as e:
            error_msg = f"Failed to acquire token for server '{self.server_name}': {e}"
            logger.error(error_msg)
            raise TokenAcquisitionError(error_msg) from e
        except (KeyError, ValueError) as e:
            error_msg = f"Invalid token response for server '{self.server_name}': {e}"
            logger.error(error_msg)
            raise TokenAcquisitionError(error_msg) from e
