"""Generic OAuth2 client credentials provider."""
import requests

from src.error_codes import ErrorCode, NetworkError
from src.oauth_providers.base import OAuthProvider, OAuthToken, TokenAcquisitionError

# Token configuration constants (shared with token_manager)
TOKEN_REQUEST_TIMEOUT_SECONDS = 30
DEFAULT_TOKEN_EXPIRY_SECONDS = 3600


class GenericOAuth2Provider(OAuthProvider):
    """
    Generic OAuth2 client credentials flow provider.

    Works with any OAuth2-compliant provider that supports
    the client credentials grant type.
    """

    @property
    def provider_name(self) -> str:
        return "generic-oauth2"

    def acquire_token(self) -> OAuthToken:
        """Acquire token using client credentials flow."""
        data = {
            "grant_type": "client_credentials",
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
        }

        if self.config.scope:
            data["scope"] = self.config.scope

        try:
            # Use injected HTTP client instead of requests directly
            response = self.http_client.post(
                url=self.config.token_endpoint,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                verify=self.config.verify_ssl,
                timeout=TOKEN_REQUEST_TIMEOUT_SECONDS,
            )

            # Parse token from response
            token_data = response.json_data

            if not token_data or "access_token" not in token_data:
                raise TokenAcquisitionError(
                    ErrorCode.TOKEN_INVALID_RESPONSE,
                    "Invalid token response: missing access_token",
                    details={
                        "endpoint": self.config.token_endpoint,
                        "response": token_data,
                    },
                )

            return OAuthToken(
                access_token=token_data["access_token"],
                expires_in=token_data.get("expires_in", DEFAULT_TOKEN_EXPIRY_SECONDS),
                token_type=token_data.get("token_type", "Bearer"),
                refresh_token=token_data.get("refresh_token"),
                scope=token_data.get("scope"),
            )

        except requests.Timeout as e:
            raise NetworkError(
                ErrorCode.NETWORK_TIMEOUT,
                f"Connection timeout to token endpoint: {e}",
                details={
                    "endpoint": self.config.token_endpoint,
                    "timeout_seconds": TOKEN_REQUEST_TIMEOUT_SECONDS,
                },
            ) from e
        except requests.ConnectionError as e:
            raise NetworkError(
                ErrorCode.NETWORK_CONNECTION_ERROR,
                f"Connection failed to token endpoint: {e}",
                details={"endpoint": self.config.token_endpoint},
            ) from e
        except requests.RequestException as e:
            raise TokenAcquisitionError(
                ErrorCode.TOKEN_ACQUISITION_FAILED,
                f"Failed to acquire token: {e}",
                details={"endpoint": self.config.token_endpoint, "error": str(e)},
            ) from e

    def validate_token(self, token: str) -> bool:
        """Generic provider doesn't validate tokens."""
        return True  # Override in provider-specific implementations

    def refresh_token(self, refresh_token: str) -> OAuthToken:
        """Refresh access token."""
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
        }

        try:
            # Use injected HTTP client instead of requests directly
            response = self.http_client.post(
                url=self.config.token_endpoint,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                verify=self.config.verify_ssl,
                timeout=TOKEN_REQUEST_TIMEOUT_SECONDS,
            )

            # Parse token from response
            token_data = response.json_data

            if not token_data or "access_token" not in token_data:
                raise TokenAcquisitionError(
                    ErrorCode.TOKEN_INVALID_RESPONSE,
                    "Invalid token response: missing access_token",
                    details={
                        "endpoint": self.config.token_endpoint,
                        "operation": "refresh",
                        "response": token_data,
                    },
                )

            return OAuthToken(
                access_token=token_data["access_token"],
                expires_in=token_data.get("expires_in", DEFAULT_TOKEN_EXPIRY_SECONDS),
                token_type=token_data.get("token_type", "Bearer"),
                refresh_token=token_data.get("refresh_token", refresh_token),
                scope=token_data.get("scope"),
            )

        except requests.Timeout as e:
            raise NetworkError(
                ErrorCode.NETWORK_TIMEOUT,
                f"Connection timeout to token endpoint during refresh: {e}",
                details={
                    "endpoint": self.config.token_endpoint,
                    "timeout_seconds": TOKEN_REQUEST_TIMEOUT_SECONDS,
                    "operation": "refresh",
                },
            ) from e
        except requests.ConnectionError as e:
            raise NetworkError(
                ErrorCode.NETWORK_CONNECTION_ERROR,
                f"Connection failed to token endpoint during refresh: {e}",
                details={
                    "endpoint": self.config.token_endpoint,
                    "operation": "refresh",
                },
            ) from e
        except requests.RequestException as e:
            raise TokenAcquisitionError(
                ErrorCode.TOKEN_REFRESH_FAILED,
                f"Failed to refresh token: {e}",
                details={"endpoint": self.config.token_endpoint, "error": str(e)},
            ) from e
