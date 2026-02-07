from typing import Any, Dict

import pytest

from src.config_parser import ConfigParser
from src.error_codes import ConfigurationError


def test_parse_basic_server_config() -> None:
    """Test parsing a simple server configuration."""
    config = {
        "DicomWebOAuth": {
            "Servers": {
                "test-server": {
                    "Url": "https://dicom.example.com/v2/",
                    "TokenEndpoint": "https://login.example.com/oauth2/token",
                    "ClientId": "client123",
                    "ClientSecret": "secret456",
                    "Scope": "https://dicom.example.com/.default",
                }
            }
        }
    }

    parser = ConfigParser(config)
    servers = parser.get_servers()

    assert len(servers) == 1
    assert "test-server" in servers
    assert servers["test-server"]["Url"] == "https://dicom.example.com/v2/"
    assert servers["test-server"]["ClientId"] == "client123"


def test_env_var_substitution(monkeypatch: Any) -> None:
    """Test that ${VAR} patterns are replaced with environment variables."""
    monkeypatch.setenv("TEST_CLIENT_ID", "env_client_123")
    monkeypatch.setenv("TEST_SECRET", "env_secret_456")

    config = {
        "DicomWebOAuth": {
            "Servers": {
                "test-server": {
                    "Url": "https://dicom.example.com/v2/",
                    "TokenEndpoint": "https://login.example.com/oauth2/token",
                    "ClientId": "${TEST_CLIENT_ID}",
                    "ClientSecret": "${TEST_SECRET}",
                    "Scope": "https://dicom.example.com/.default",
                }
            }
        }
    }

    parser = ConfigParser(config)
    servers = parser.get_servers()

    assert servers["test-server"]["ClientId"] == "env_client_123"
    assert servers["test-server"]["ClientSecret"] == "env_secret_456"


def test_missing_env_var_raises_error(monkeypatch: Any) -> None:
    """Test that missing environment variables raise ConfigurationError."""
    config: Dict[str, Any] = {
        "DicomWebOAuth": {
            "Servers": {
                "test-server": {
                    "Url": "https://dicom.example.com/v2/",
                    "TokenEndpoint": "https://login.example.com/oauth2/token",
                    "ClientId": "${MISSING_VAR}",
                    "ClientSecret": "secret",
                    "Scope": "scope",
                }
            }
        }
    }

    with pytest.raises(ConfigurationError, match="Environment variable 'MISSING_VAR'"):
        parser = ConfigParser(config)
        parser.get_servers()


def test_missing_dicomweb_oauth_section() -> None:
    """Test that missing DicomWebOAuth section raises error."""
    config: Dict[str, Any] = {}

    with pytest.raises(ConfigurationError, match="Missing 'DicomWebOAuth' section"):
        ConfigParser(config, validate_schema=False)


def test_missing_servers_section() -> None:
    """Test that missing Servers section raises error."""
    config: Dict[str, Any] = {"DicomWebOAuth": {}}

    with pytest.raises(ConfigurationError, match="Missing 'Servers' section"):
        ConfigParser(config)
