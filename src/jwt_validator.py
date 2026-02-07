"""JWT token signature validation."""
from typing import List, Optional

import jwt
from jwt.exceptions import InvalidTokenError

from src.structured_logger import structured_logger


class JWTValidator:
    """
    Validates JWT tokens with signature verification.

    Validates:
    - Token signature using public key
    - Token expiration (exp claim)
    - Audience (aud claim)
    - Issuer (iss claim)
    - Not-before time (nbf claim, if present)

    Example:
        >>> validator = JWTValidator(
        ...     public_key=public_key_pem,
        ...     expected_audience="https://api.example.com",
        ...     expected_issuer="https://auth.example.com",
        ...     algorithms=["RS256"]
        ... )
        >>> is_valid = validator.validate(token)
    """

    def __init__(
        self,
        public_key: Optional[bytes],
        expected_audience: Optional[str] = None,
        expected_issuer: Optional[str] = None,
        algorithms: Optional[List[str]] = None,
    ) -> None:
        """
        Initialize JWT validator.

        Args:
            public_key: Public key in PEM format (None disables validation)
            expected_audience: Expected audience claim (optional)
            expected_issuer: Expected issuer claim (optional)
            algorithms: Allowed signing algorithms (default: ["RS256"])
        """
        self.public_key = public_key
        self.expected_audience = expected_audience
        self.expected_issuer = expected_issuer
        self.algorithms = algorithms or ["RS256"]

        # Validation is disabled if no public key provided
        self.enabled = public_key is not None

    def validate(self, token: str) -> bool:
        """
        Validate JWT token signature and claims.

        Args:
            token: JWT token string

        Returns:
            True if token is valid, False otherwise
        """
        if not self.enabled:
            # Validation disabled
            return True

        try:
            # Decode and verify token
            decoded = jwt.decode(
                token,
                key=self.public_key,
                algorithms=self.algorithms,
                audience=self.expected_audience,
                issuer=self.expected_issuer,
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_nbf": True,
                    "verify_aud": self.expected_audience is not None,
                    "verify_iss": self.expected_issuer is not None,
                },
            )

            structured_logger.debug(
                "JWT validation successful",
                operation="jwt_validate",
                algorithm=decoded.get("alg"),
                issuer=decoded.get("iss"),
                audience=decoded.get("aud"),
            )

            return True

        except InvalidTokenError as e:
            structured_logger.warning(
                "JWT validation failed",
                operation="jwt_validate",
                error_type=type(e).__name__,
                error_message=str(e),
            )
            return False

        except Exception as e:
            structured_logger.error(
                "Unexpected error during JWT validation",
                operation="jwt_validate",
                error_type=type(e).__name__,
                error_message=str(e),
            )
            return False
