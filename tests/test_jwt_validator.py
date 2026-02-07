"""Tests for JWT signature validation."""
from datetime import datetime, timedelta, timezone
from typing import Any, Generator, Tuple

import jwt
import pytest

from src.jwt_validator import JWTValidator


@pytest.fixture  # type: ignore[misc]
def rsa_keys() -> Generator[Tuple[Any, bytes], None, None]:
    """Generate RSA key pair for testing."""
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

    private_key = rsa.generate_private_key(
        public_exponent=65537, key_size=2048, backend=default_backend()
    )

    public_key = private_key.public_key()

    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    yield private_key, public_pem


def test_validate_valid_jwt(rsa_keys: Tuple[Any, bytes]) -> None:
    """Test validation of a valid JWT token."""
    private_key, public_key = rsa_keys

    # Create validator
    validator = JWTValidator(
        public_key=public_key,
        expected_audience="test-audience",
        expected_issuer="test-issuer",
        algorithms=["RS256"],
    )

    # Create valid token
    payload = {
        "aud": "test-audience",
        "iss": "test-issuer",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        "iat": datetime.now(timezone.utc),
    }
    token = jwt.encode(payload, private_key, algorithm="RS256")

    # Should validate successfully
    result = validator.validate(token)
    assert result is True


def test_validate_expired_jwt(rsa_keys: Tuple[Any, bytes]) -> None:
    """Test validation fails for expired token."""
    private_key, public_key = rsa_keys

    validator = JWTValidator(
        public_key=public_key,
        expected_audience="test-audience",
        expected_issuer="test-issuer",
        algorithms=["RS256"],
    )

    # Create expired token
    payload = {
        "aud": "test-audience",
        "iss": "test-issuer",
        "exp": datetime.now(timezone.utc) - timedelta(hours=1),  # Expired
        "iat": datetime.now(timezone.utc) - timedelta(hours=2),
    }
    token = jwt.encode(payload, private_key, algorithm="RS256")

    # Should fail validation
    result = validator.validate(token)
    assert result is False


def test_validate_wrong_audience(rsa_keys: Tuple[Any, bytes]) -> None:
    """Test validation fails for wrong audience."""
    private_key, public_key = rsa_keys

    validator = JWTValidator(
        public_key=public_key,
        expected_audience="test-audience",
        expected_issuer="test-issuer",
        algorithms=["RS256"],
    )

    # Create token with wrong audience
    payload = {
        "aud": "wrong-audience",
        "iss": "test-issuer",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        "iat": datetime.now(timezone.utc),
    }
    token = jwt.encode(payload, private_key, algorithm="RS256")

    # Should fail validation
    result = validator.validate(token)
    assert result is False


def test_validate_wrong_issuer(rsa_keys: Tuple[Any, bytes]) -> None:
    """Test validation fails for wrong issuer."""
    private_key, public_key = rsa_keys

    validator = JWTValidator(
        public_key=public_key,
        expected_audience="test-audience",
        expected_issuer="test-issuer",
        algorithms=["RS256"],
    )

    # Create token with wrong issuer
    payload = {
        "aud": "test-audience",
        "iss": "wrong-issuer",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        "iat": datetime.now(timezone.utc),
    }
    token = jwt.encode(payload, private_key, algorithm="RS256")

    # Should fail validation
    result = validator.validate(token)
    assert result is False


def test_validate_tampered_token(rsa_keys: Tuple[Any, bytes]) -> None:
    """Test validation fails for tampered token."""
    private_key, public_key = rsa_keys

    validator = JWTValidator(
        public_key=public_key,
        expected_audience="test-audience",
        expected_issuer="test-issuer",
        algorithms=["RS256"],
    )

    # Create valid token
    payload = {
        "aud": "test-audience",
        "iss": "test-issuer",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        "iat": datetime.now(timezone.utc),
    }
    token = jwt.encode(payload, private_key, algorithm="RS256")

    # Tamper with token (change payload)
    parts = token.split(".")
    tampered_token = parts[0] + ".TAMPERED." + parts[2]

    # Should fail validation
    result = validator.validate(tampered_token)
    assert result is False


def test_validation_disabled() -> None:
    """Test that validation can be disabled."""
    validator = JWTValidator(
        public_key=None,  # No key = validation disabled
        expected_audience="test-audience",
        expected_issuer="test-issuer",
    )

    # Any token should pass when disabled
    result = validator.validate("any.invalid.token")
    assert result is True
