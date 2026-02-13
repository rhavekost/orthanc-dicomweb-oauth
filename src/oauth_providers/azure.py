"""Azure Active Directory (Entra ID) OAuth provider."""
from typing import TYPE_CHECKING, Any, Dict, Optional

import jwt
from jwt import PyJWKClient  # type: ignore[attr-defined]

from src.jwt_validator import JWTValidator
from src.oauth_providers.base import OAuthConfig, OAuthProvider
from src.oauth_providers.generic import GenericOAuth2Provider
from src.structured_logger import structured_logger

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
        config: Dict[str, Any],
        tenant_id: Optional[str] = None,
        http_client: Optional["HttpClient"] = None,
    ):
        """
        Initialize Azure OAuth provider.

        Args:
            config: Dict configuration or OAuthConfig
            tenant_id: Optional tenant ID (extracted from config if not provided)
            http_client: Optional HTTP client
        """
        # Support both Dict and OAuthConfig
        if isinstance(config, dict):
            tenant_id = tenant_id or config.get("TenantId", "common")
            # Call parent with dict config (GenericOAuth2Provider handles conversion)
            # But we need to bypass parent's __init__ to avoid double init
            # So we'll duplicate the logic here
            oauth_config = OAuthConfig(
                token_endpoint=config["TokenEndpoint"],
                client_id=config["ClientId"],
                client_secret=config["ClientSecret"],
                scope=config.get("Scope", ""),
                verify_ssl=config.get("VerifySSL", True),
            )
        else:
            oauth_config = config
            tenant_id = tenant_id or "common"

        # Call OAuthProvider.__init__ directly
        OAuthProvider.__init__(self, oauth_config, http_client)

        self.tenant_id = tenant_id
        self.jwks_uri = (
            f"https://login.microsoftonline.com/{tenant_id}/discovery/v2.0/keys"
        )
        self.issuer = f"https://login.microsoftonline.com/{tenant_id}/v2.0"

        # Initialize JWT validator for Azure
        if isinstance(config, dict):
            jwt_public_key = config.get("JWTPublicKey")
            jwt_audience = config.get("JWTAudience")
            jwt_issuer = config.get("JWTIssuer")

            self.jwt_validator = JWTValidator(
                public_key=jwt_public_key.encode() if jwt_public_key else None,
                expected_audience=jwt_audience,
                expected_issuer=jwt_issuer,
                algorithms=["RS256"],  # Azure uses RS256
            )

            if self.jwt_validator.enabled:
                structured_logger.info(
                    "JWT validation enabled for Azure",
                    provider=self.provider_name,
                    audience=jwt_audience,
                    issuer=jwt_issuer,
                )
        else:
            # No JWT validator for OAuthConfig-based init
            self.jwt_validator = JWTValidator(public_key=None)

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
