"""Google Cloud Healthcare API OAuth2 provider."""

from typing import Any, Dict, Optional

from src.error_codes import ErrorCode
from src.oauth_providers.base import OAuthToken, TokenAcquisitionError
from src.oauth_providers.generic import GenericOAuth2Provider
from src.structured_logger import structured_logger


class GoogleProvider(GenericOAuth2Provider):
    """OAuth2 provider for Google Cloud Healthcare API."""

    provider_name = "google"

    def __init__(self, config: Dict[str, Any], http_client: Optional[Any] = None):
        """Initialize Google provider."""
        super().__init__(config, http_client)

        # Default Google OAuth2 endpoint
        if not self.config.token_endpoint:
            self.config.token_endpoint = "https://oauth2.googleapis.com/token"

        # Validate scope
        if (
            self.config.scope
            and "googleapis.com/auth/cloud-healthcare" not in self.config.scope
        ):
            structured_logger.warning(
                "Scope may not work with Google Healthcare API",
                scope=self.config.scope,
                recommended_scope="https://www.googleapis.com/auth/cloud-healthcare",
            )

    def acquire_token(self) -> OAuthToken:
        """Acquire access token from Google OAuth2."""
        structured_logger.info("acquiring_token", provider="google")

        try:
            # Use parent class's acquire_token implementation
            token = super().acquire_token()

            structured_logger.info("token_acquired", provider="google")
            return token

        except TokenAcquisitionError as e:
            # Enhance error with Google-specific context
            structured_logger.error(
                "token_acquisition_failed", provider="google", error=str(e)
            )
            raise
        except Exception as e:
            structured_logger.error("unexpected_error", provider="google", error=str(e))
            raise TokenAcquisitionError(
                ErrorCode.TOKEN_ACQUISITION_FAILED,
                f"Google token acquisition failed: {e}",
            )
