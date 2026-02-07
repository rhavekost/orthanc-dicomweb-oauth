"""Tests for configuration schema validation."""
import pytest

from src.config_parser import ConfigParser
from src.error_codes import ConfigurationError


def test_valid_config_passes_validation() -> None:
    """Test that valid configuration passes schema validation."""
    config = {
        "DicomWebOAuth": {
            "Servers": {
                "server1": {
                    "Url": "https://pacs.example.com/dicomweb",
                    "TokenEndpoint": "https://login.example.com/token",
                    "ClientId": "client123",
                    "ClientSecret": "secret456",
                    "Scope": "api",
                    "VerifySSL": True,
                }
            }
        }
    }

    parser = ConfigParser(config)
    servers = parser.get_servers()

    assert "server1" in servers
    assert servers["server1"]["ClientId"] == "client123"


def test_missing_required_field_fails_validation() -> None:
    """Test that missing required fields fail validation."""
    config = {
        "DicomWebOAuth": {
            "Servers": {
                "server1": {
                    "Url": "https://pacs.example.com/dicomweb",
                    "TokenEndpoint": "https://login.example.com/token",
                    # Missing ClientId and ClientSecret
                    "Scope": "api",
                }
            }
        }
    }

    with pytest.raises(ConfigurationError) as exc_info:
        ConfigParser(config)

    assert (
        "ClientId" in str(exc_info.value) or "required" in str(exc_info.value).lower()
    )


def test_invalid_type_fails_validation() -> None:
    """Test that invalid field types fail validation."""
    config = {
        "DicomWebOAuth": {
            "Servers": {
                "server1": {
                    "Url": "https://pacs.example.com/dicomweb",
                    "TokenEndpoint": "https://login.example.com/token",
                    "ClientId": "client123",
                    "ClientSecret": "secret456",
                    "VerifySSL": "yes",  # Should be boolean
                }
            }
        }
    }

    with pytest.raises(ConfigurationError) as exc_info:
        ConfigParser(config)

    assert (
        "VerifySSL" in str(exc_info.value) or "boolean" in str(exc_info.value).lower()
    )


def test_invalid_url_format_fails_validation() -> None:
    """Test that invalid URLs fail validation."""
    config = {
        "DicomWebOAuth": {
            "Servers": {
                "server1": {
                    "Url": "not-a-valid-url",
                    "TokenEndpoint": "also-invalid",
                    "ClientId": "client123",
                    "ClientSecret": "secret456",
                }
            }
        }
    }

    with pytest.raises(ConfigurationError) as exc_info:
        ConfigParser(config)

    assert (
        "url" in str(exc_info.value).lower() or "format" in str(exc_info.value).lower()
    )
