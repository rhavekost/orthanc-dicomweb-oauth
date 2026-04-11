"""Azure Active Directory (Entra ID) OAuth provider."""
import logging
from typing import TYPE_CHECKING, Any, Dict, Optional

import jwt as pyjwt
from jwt.exceptions import InvalidTokenError
from jwt.jwks_client import PyJWKClient as _PyJWKClient

from src.jwt_validator import JWTValidator
from src.oauth_providers.base import OAuthConfig
from src.oauth_providers.generic import GenericOAuth2Provider
from src.structured_logger import structured_logger

if TYPE_CHECKING:
    from src.http_client import HttpClient

logger = logging.getLogger(__name__)


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

        # Call GenericOAuth2Provider with OAuthConfig (not dict) to avoid
        # duplicating dict→OAuthConfig conversion logic
        super().__init__(oauth_config, http_client)

        self.tenant_id = tenant_id
        self.jwks_uri = (
            f"https://login.microsoftonline.com/{tenant_id}/discovery/v2.0/keys"
        )
        self.issuer = f"https://login.microsoftonline.com/{tenant_id}/v2.0"

        # Cache the JWKS client so validate_token reuses fetched keys across
        # calls rather than making a network round-trip on every invocation.
        # PyJWKClient (PyJWT >= 2.4) uses an internal threading.Lock for its
        # key cache, so concurrent calls to get_signing_key_from_jwt are safe.
        self._jwks_client = _PyJWKClient(self.jwks_uri)

        # The 'common' endpoint issues tokens whose 'iss' contains the real
        # tenant GUID, never the literal string 'common'. Issuer verification
        # against a static self.issuer would always fail for common-tenant
        # deployments, so we disable it and rely on signature + expiry checks.
        self._verify_issuer = tenant_id != "common"

        # Derive audience from scope: strip /.default suffix for aud validation.
        # Azure client-credentials scopes are typically <resource>/.default and
        # the token aud claim is the bare resource URL.
        # If scope has no /.default suffix, audience verification is skipped and
        # a warning is emitted below to make the degraded validation visible.
        self._expected_audience: Optional[str] = None
        scope = oauth_config.scope
        if scope and scope.endswith("/.default"):
            self._expected_audience = scope.rsplit("/.default", 1)[0]

        # Check if JWT validation is explicitly disabled in config
        self._jwt_validation_disabled = False
        if isinstance(config, dict):
            self._jwt_validation_disabled = config.get("DisableJWTValidation", False)

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

        # Warn when defaulting to 'common' tenant (no issuer verification)
        if tenant_id == "common":
            structured_logger.warning(
                "Azure OAuth using multi-tenant 'common' endpoint. "
                "Healthcare deployments should specify a tenant_id for "
                "tenant-specific token validation.",
                provider=self.provider_name,
                tenant_id=tenant_id,
            )

        # Warn when audience verification will be skipped. This happens when
        # Scope does not end in '/.default' so _expected_audience is None.
        # Without audience checking, any token signed by Azure JWKS keys will
        # pass, including tokens issued for unrelated resources (e.g. MS Graph).
        # To silence this warning, use a scope ending in '/.default' or set
        # DisableJWTValidation=true if you explicitly accept signature-only checks.
        if not self._jwt_validation_disabled and self._expected_audience is None:
            structured_logger.warning(
                "Azure JWT audience verification is disabled because Scope does "
                "not end in '/.default'. Tokens for any Azure resource will pass "
                "validation. Use a '/.default' scope to enable audience checking.",
                provider=self.provider_name,
                scope=scope,
            )

    @property
    def provider_name(self) -> str:
        return "azure-ad"

    def validate_token(self, token: str) -> bool:
        """
        Validate JWT signature using Azure's JWKS.

        For client credentials flow tokens:
        - aud is set to the resource URL (e.g. https://dicom.healthcareapis.azure.com)
        - iss is the tenant-specific URL
        - Validates token is not expired

        Falls back to True if JWT validation is explicitly disabled.
        """
        # If JWT validation is explicitly disabled, skip
        if self._jwt_validation_disabled:
            structured_logger.debug(
                "JWT validation explicitly disabled",
                provider=self.provider_name,
            )
            return True

        # If a static JWTPublicKey was provided, use the existing JWTValidator
        if hasattr(self, "jwt_validator") and self.jwt_validator.enabled:
            result: bool = self.jwt_validator.validate(token)
            return result

        # Attempt JWKS-based validation using the cached client (no per-call
        # network fetch unless the key has rotated).
        try:
            signing_key = self._jwks_client.get_signing_key_from_jwt(token)

            decode_options = {
                "verify_signature": True,
                "verify_exp": True,
                "verify_nbf": True,
                "verify_aud": self._expected_audience is not None,
                # Skip issuer check for 'common' tenant: Azure tokens carry
                # the real tenant GUID in 'iss', not the literal 'common'.
                "verify_iss": self._verify_issuer,
            }

            pyjwt.decode(
                token,
                key=signing_key.key,
                algorithms=["RS256"],
                audience=self._expected_audience,
                issuer=self.issuer if self._verify_issuer else None,
                options=decode_options,
            )

            structured_logger.debug(
                "Azure JWT validation successful",
                provider=self.provider_name,
                issuer=self.issuer if self._verify_issuer else "common (not verified)",
                audience=self._expected_audience,
            )
            return True

        except InvalidTokenError as e:
            structured_logger.warning(
                "Azure JWT validation failed",
                provider=self.provider_name,
                error_type=type(e).__name__,
                error_message=str(e),
            )
            return False

        except Exception as e:
            structured_logger.error(
                "Unexpected error during Azure JWT validation",
                provider=self.provider_name,
                error_type=type(e).__name__,
                error_message=str(e),
            )
            return False
