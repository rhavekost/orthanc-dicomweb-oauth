"""Azure Active Directory (Entra ID) OAuth provider."""
from typing import TYPE_CHECKING, Optional

import jwt
from jwt import PyJWKClient

from src.oauth_providers.base import OAuthConfig
from src.oauth_providers.generic import GenericOAuth2Provider

if TYPE_CHECKING:
    from src.http_client import HttpClient


class AzureOAuthProvider(GenericOAuth2Provider):
    """
    Azure AD (Entra ID) OAuth provider.

    Adds Azure-specific features:
    - JWT signature validation using Azure's JWKS endpoint
    - Azure-specific token endpoints
    - Tenant-aware configuration
    """

    def __init__(
        self,
        config: OAuthConfig,
        tenant_id: str,
        http_client: Optional["HttpClient"] = None,
    ):
        super().__init__(config, http_client=http_client)
        self.tenant_id = tenant_id
        self.jwks_uri = (
            f"https://login.microsoftonline.com/{tenant_id}/discovery/v2.0/keys"
        )
        self.issuer = f"https://login.microsoftonline.com/{tenant_id}/v2.0"

    @property
    def provider_name(self) -> str:
        return "azure-ad"

    def validate_token(self, token: str) -> bool:
        """Validate JWT signature using Azure's JWKS."""
        try:
            jwks_client = PyJWKClient(self.jwks_uri)
            signing_key = jwks_client.get_signing_key_from_jwt(token)

            jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=self.config.client_id,
                issuer=self.issuer,
            )
            return True

        except jwt.InvalidTokenError:
            return False
