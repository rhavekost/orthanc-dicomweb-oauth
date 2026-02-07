"""Generic OAuth2 client credentials provider."""
from typing import Any, Optional

import requests

from src.error_codes import ErrorCode, NetworkError
from src.jwt_validator import JWTValidator
from src.oauth_providers.base import (
    OAuthConfig,
    OAuthProvider,
    OAuthToken,
    TokenAcquisitionError,
)
from src.structured_logger import structured_logger

# Token configuration constants (shared with token_manager)
TOKEN_REQUEST_TIMEOUT_SECONDS = 30
DEFAULT_TOKEN_EXPIRY_SECONDS = 3600


class GenericOAuth2Provider(OAuthProvider):
    """
    Generic OAuth2 client credentials flow provider.

    Works with any OAuth2-compliant provider that supports
    the client credentials grant type.
    """

    def __init__(self, config: Any, http_client: Optional[Any] = None) -> None:
        """
        Initialize generic OAuth provider.

        Args:
            config: Dict configuration or OAuthConfig
            http_client: Optional HTTP client
        """
        # Support both Dict and OAuthConfig
        if isinstance(config, dict):
            # Dict config - convert to OAuthConfig
            oauth_config = OAuthConfig(
                token_endpoint=config["TokenEndpoint"],
                client_id=config["ClientId"],
                client_secret=config["ClientSecret"],
                scope=config.get("Scope", ""),
                verify_ssl=config.get("VerifySSL", True),
            )

            # Call parent init
            super().__init__(oauth_config, http_client)

            # Initialize JWT validator if configured (only for dict config)
            jwt_public_key = config.get("JWTPublicKey")
            jwt_audience = config.get("JWTAudience")
            jwt_issuer = config.get("JWTIssuer")
            jwt_algorithms = config.get("JWTAlgorithms", ["RS256"])

            self.jwt_validator = JWTValidator(
                public_key=jwt_public_key.encode() if jwt_public_key else None,
                expected_audience=jwt_audience,
                expected_issuer=jwt_issuer,
                algorithms=jwt_algorithms
                if isinstance(jwt_algorithms, list)
                else [jwt_algorithms],
            )

            if self.jwt_validator.enabled:
                structured_logger.info(
                    "JWT validation enabled",
                    provider=self.provider_name,
                    audience=jwt_audience,
                    issuer=jwt_issuer,
                    algorithms=jwt_algorithms,
                )
        else:
            # OAuthConfig - use as-is
            super().__init__(config, http_client)
            # No JWT validator for OAuthConfig-based init
            self.jwt_validator = JWTValidator(public_key=None)

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
