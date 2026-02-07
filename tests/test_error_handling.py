from typing import Any, Dict

import pytest
import responses
from requests.exceptions import Timeout

from src.config_parser import ConfigParser
from src.error_codes import (
    ConfigurationError,
    ErrorCode,
    NetworkError,
    TokenAcquisitionError,
)
from src.token_manager import TokenManager


@responses.activate  # type: ignore[misc]
def test_retry_on_timeout() -> None:
    """Test that token acquisition retries on timeout."""
    # First attempt times out
    responses.add(
        responses.POST,
        "https://login.example.com/oauth2/token",
        body=Timeout("Connection timeout"),
    )

    # Second attempt succeeds
    responses.add(
        responses.POST,
        "https://login.example.com/oauth2/token",
        json={"access_token": "token123", "token_type": "Bearer", "expires_in": 3600},
        status=200,
    )

    config = {
        "TokenEndpoint": "https://login.example.com/oauth2/token",
        "ClientId": "client123",
        "ClientSecret": "secret456",
        "Scope": "scope",
    }

    manager = TokenManager("test-server", config)
    token = manager.get_token()

    assert token == "token123"
    assert len(responses.calls) == 2  # Retried once


@responses.activate  # type: ignore[misc]
def test_max_retries_exceeded() -> None:
    """Test that token acquisition fails after max retries."""
    # All attempts time out
    for _ in range(3):
        responses.add(
            responses.POST,
            "https://login.example.com/oauth2/token",
            body=Timeout("Connection timeout"),
        )

    config = {
        "TokenEndpoint": "https://login.example.com/oauth2/token",
        "ClientId": "client123",
        "ClientSecret": "secret456",
        "Scope": "scope",
    }

    manager = TokenManager("test-server", config)

    with pytest.raises(TokenAcquisitionError, match="after 3 attempts"):
        manager.get_token()

    assert len(responses.calls) == 3  # All retries attempted


@responses.activate  # type: ignore[misc]
def test_no_retry_on_auth_error() -> None:
    """Test that 401 authentication errors are not retried."""
    responses.add(
        responses.POST,
        "https://login.example.com/oauth2/token",
        json={"error": "invalid_client"},
        status=401,
    )

    config = {
        "TokenEndpoint": "https://login.example.com/oauth2/token",
        "ClientId": "invalid_client",
        "ClientSecret": "wrong_secret",
        "Scope": "scope",
    }

    manager = TokenManager("test-server", config)

    with pytest.raises(TokenAcquisitionError):
        manager.get_token()

    # Should not retry auth errors
    assert len(responses.calls) == 1


def test_config_error_includes_error_code() -> None:
    """Test configuration errors include structured error codes."""
    config: Dict[str, Any] = {"DicomWebOAuth": {"Servers": {}}}

    with pytest.raises(ConfigurationError) as exc_info:
        parser = ConfigParser(config)
        parser.get_servers()

    error = exc_info.value
    # Schema validation will catch empty Servers as CONFIG_INVALID_VALUE
    assert error.error_code == ErrorCode.CONFIG_INVALID_VALUE
    assert "troubleshooting" in error.to_dict()
    assert error.documentation_url is not None


def test_config_missing_key_error_code() -> None:
    """Test missing DicomWebOAuth section returns CONFIG_MISSING_KEY."""
    config: Dict[str, Any] = {}

    with pytest.raises(ConfigurationError) as exc_info:
        ConfigParser(config, validate_schema=False)

    error = exc_info.value
    assert error.error_code == ErrorCode.CONFIG_MISSING_KEY
    assert "DicomWebOAuth" in error.message
    assert "troubleshooting" in error.to_dict()
    assert error.documentation_url is not None


@responses.activate  # type: ignore[misc]
def test_token_acquisition_error_includes_error_code() -> None:
    """Test token acquisition errors include structured error codes after retries."""
    # Simulate persistent network timeout across all retry attempts
    for _ in range(3):  # MAX_TOKEN_ACQUISITION_RETRIES = 3
        responses.add(
            responses.POST,
            "https://test.com/token",
            body=Timeout("Connection timeout"),
        )

    config = {
        "TokenEndpoint": "https://test.com/token",
        "ClientId": "test-id",
        "ClientSecret": "test-secret",
    }

    manager = TokenManager("test-server", config)

    # After exhausting retries, TokenAcquisitionError is raised (wrapping NetworkError)
    with pytest.raises(TokenAcquisitionError) as exc_info:
        manager.get_token()

    error = exc_info.value
    assert error.error_code == ErrorCode.TOKEN_ACQUISITION_FAILED
    assert "troubleshooting" in error.to_dict()
    assert error.documentation_url is not None
    # Should have wrapped the original NetworkError
    assert isinstance(error.__cause__, NetworkError)
