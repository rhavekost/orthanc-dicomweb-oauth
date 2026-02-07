"""AWS HealthImaging OAuth2 provider."""

from typing import Any, Dict, Optional

from src.error_codes import ErrorCode
from src.oauth_providers.base import OAuthToken, TokenAcquisitionError
from src.oauth_providers.generic import GenericOAuth2Provider
from src.structured_logger import structured_logger


class AWSProvider(GenericOAuth2Provider):
    """OAuth2 provider for AWS HealthImaging.

    Note: AWS uses Signature Version 4, not traditional OAuth2.
    This provider adapts AWS authentication to the OAuth provider interface.
    This is a basic implementation - full Signature v4 implementation pending.
    """

    provider_name = "aws"

    def __init__(self, config: Dict[str, Any], http_client: Optional[Any] = None):
        """Initialize AWS provider."""
        super().__init__(config, http_client)

        self.region = config.get("Region", "us-west-2")
        self.use_instance_profile = config.get("UseInstanceProfile", False)
        self.service = "medical-imaging"
        self._session_token = None

        if self.use_instance_profile:
            structured_logger.info(
                "Instance profile support not yet implemented", provider="aws"
            )

    def acquire_token(self) -> OAuthToken:
        """Acquire AWS credentials as token.

        AWS doesn't use traditional OAuth2 tokens.
        Returns credentials that can be used for request signing.
        """
        structured_logger.info("acquiring_token", provider="aws", region=self.region)

        try:
            # For now, use parent class implementation for client credentials flow
            # Full AWS Signature v4 implementation would go here
            token = super().acquire_token()

            structured_logger.info("token_acquired", provider="aws")
            return token

        except TokenAcquisitionError as e:
            structured_logger.error(
                "token_acquisition_failed", provider="aws", error=str(e)
            )
            raise
        except Exception as e:
            structured_logger.error("unexpected_error", provider="aws", error=str(e))
            raise TokenAcquisitionError(
                ErrorCode.TOKEN_ACQUISITION_FAILED, f"AWS authentication failed: {e}"
            )
