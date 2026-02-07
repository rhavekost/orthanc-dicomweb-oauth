"""Tests for security configuration schema."""
from typing import Any, Dict

import pytest
from jsonschema import ValidationError, validate

from src.config_schema import load_schema


def test_schema_accepts_jwt_public_key() -> None:
    """Test that schema accepts JWT public key configuration."""
    config: Dict[str, Any] = {
        "DicomWebOAuth": {
            "Servers": {
                "test-server": {
                    "Url": "https://dicom.example.com",
                    "TokenEndpoint": "https://auth.example.com/token",
                    "ClientId": "test-client",
                    "ClientSecret": "test-secret",
                    "JWTPublicKey": (
                        "-----BEGIN PUBLIC KEY-----\n...\n-----END PUBLIC KEY-----"
                    ),
                    "JWTAudience": "https://api.example.com",
                    "JWTIssuer": "https://auth.example.com",
                }
            }
        }
    }

    schema = load_schema()
    # Should not raise ValidationError
    validate(instance=config, schema=schema)


def test_schema_accepts_jwt_algorithms() -> None:
    """Test that schema accepts JWT algorithms configuration."""
    config: Dict[str, Any] = {
        "DicomWebOAuth": {
            "Servers": {
                "test-server": {
                    "Url": "https://dicom.example.com",
                    "TokenEndpoint": "https://auth.example.com/token",
                    "ClientId": "test-client",
                    "ClientSecret": "test-secret",
                    "JWTAlgorithms": ["RS256", "RS384"],
                }
            }
        }
    }

    schema = load_schema()
    validate(instance=config, schema=schema)


def test_schema_accepts_single_jwt_algorithm() -> None:
    """Test that schema accepts single JWT algorithm as string."""
    config: Dict[str, Any] = {
        "DicomWebOAuth": {
            "Servers": {
                "test-server": {
                    "Url": "https://dicom.example.com",
                    "TokenEndpoint": "https://auth.example.com/token",
                    "ClientId": "test-client",
                    "ClientSecret": "test-secret",
                    "JWTAlgorithms": "RS256",
                }
            }
        }
    }

    schema = load_schema()
    validate(instance=config, schema=schema)


def test_schema_accepts_rate_limit_config() -> None:
    """Test that schema accepts rate limit configuration."""
    config: Dict[str, Any] = {
        "DicomWebOAuth": {
            "RateLimitRequests": 10,
            "RateLimitWindowSeconds": 60,
            "Servers": {
                "test-server": {
                    "Url": "https://dicom.example.com",
                    "TokenEndpoint": "https://auth.example.com/token",
                    "ClientId": "test-client",
                    "ClientSecret": "test-secret",
                }
            },
        }
    }

    schema = load_schema()
    validate(instance=config, schema=schema)


def test_schema_rejects_invalid_rate_limit() -> None:
    """Test that schema rejects invalid rate limit values."""
    config: Dict[str, Any] = {
        "DicomWebOAuth": {
            "RateLimitRequests": -1,  # Invalid: must be positive
            "Servers": {
                "test-server": {
                    "Url": "https://dicom.example.com",
                    "TokenEndpoint": "https://auth.example.com/token",
                    "ClientId": "test-client",
                    "ClientSecret": "test-secret",
                }
            },
        }
    }

    schema = load_schema()
    with pytest.raises(ValidationError):
        validate(instance=config, schema=schema)


def test_schema_rejects_zero_rate_limit() -> None:
    """Test that schema rejects zero rate limit."""
    config: Dict[str, Any] = {
        "DicomWebOAuth": {
            "RateLimitRequests": 0,  # Invalid: must be at least 1
            "Servers": {
                "test-server": {
                    "Url": "https://dicom.example.com",
                    "TokenEndpoint": "https://auth.example.com/token",
                    "ClientId": "test-client",
                    "ClientSecret": "test-secret",
                }
            },
        }
    }

    schema = load_schema()
    with pytest.raises(ValidationError):
        validate(instance=config, schema=schema)


def test_schema_jwt_public_key_optional() -> None:
    """Test that JWT configuration is optional."""
    config: Dict[str, Any] = {
        "DicomWebOAuth": {
            "Servers": {
                "test-server": {
                    "Url": "https://dicom.example.com",
                    "TokenEndpoint": "https://auth.example.com/token",
                    "ClientId": "test-client",
                    "ClientSecret": "test-secret",
                    # No JWT config - should still be valid
                }
            }
        }
    }

    schema = load_schema()
    validate(instance=config, schema=schema)


def test_schema_rate_limit_optional() -> None:
    """Test that rate limit configuration is optional."""
    config: Dict[str, Any] = {
        "DicomWebOAuth": {
            "Servers": {
                "test-server": {
                    "Url": "https://dicom.example.com",
                    "TokenEndpoint": "https://auth.example.com/token",
                    "ClientId": "test-client",
                    "ClientSecret": "test-secret",
                }
            }
            # No rate limit config - should still be valid
        }
    }

    schema = load_schema()
    validate(instance=config, schema=schema)
