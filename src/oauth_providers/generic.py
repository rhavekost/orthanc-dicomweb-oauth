"""Generic OAuth2 client credentials provider."""
import requests

from src.oauth_providers.base import OAuthProvider, OAuthToken, TokenAcquisitionError


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
            response = requests.post(
                self.config.token_endpoint,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=30,
                verify=self.config.verify_ssl,
            )
            response.raise_for_status()

            token_data = response.json()
            return OAuthToken(
                access_token=token_data["access_token"],
                expires_in=token_data.get("expires_in", 3600),
                token_type=token_data.get("token_type", "Bearer"),
                refresh_token=token_data.get("refresh_token"),
                scope=token_data.get("scope"),
            )

        except (requests.Timeout, requests.ConnectionError):
            # Let timeout/connection errors bubble up for retry logic
            raise
        except requests.RequestException as e:
            # Wrap other request exceptions (auth errors, etc.)
            raise TokenAcquisitionError(f"Failed to acquire token: {e}") from e
        except (KeyError, ValueError) as e:
            raise TokenAcquisitionError(f"Invalid token response: {e}") from e

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
            response = requests.post(
                self.config.token_endpoint,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=30,
                verify=self.config.verify_ssl,
            )
            response.raise_for_status()

            token_data = response.json()
            return OAuthToken(
                access_token=token_data["access_token"],
                expires_in=token_data.get("expires_in", 3600),
                token_type=token_data.get("token_type", "Bearer"),
                refresh_token=token_data.get("refresh_token", refresh_token),
                scope=token_data.get("scope"),
            )

        except (requests.Timeout, requests.ConnectionError):
            # Let timeout/connection errors bubble up for retry logic
            raise
        except requests.RequestException as e:
            raise TokenAcquisitionError(f"Failed to refresh token: {e}") from e
