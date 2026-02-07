"""Tests for structured error code system."""
from src.error_codes import (
    ConfigurationError,
    ErrorCategory,
    ErrorCode,
    ErrorSeverity,
    NetworkError,
    PluginError,
)


def test_error_code_enum_values() -> None:
    """Test that error codes have proper structure."""
    assert ErrorCode.CONFIG_MISSING_KEY.code.startswith("CFG")
    assert ErrorCode.TOKEN_ACQUISITION_FAILED.code.startswith("TOK")
    assert ErrorCode.NETWORK_TIMEOUT.code.startswith("NET")


def test_error_category_mapping() -> None:
    """Test that error codes map to categories correctly."""
    assert ErrorCode.CONFIG_MISSING_KEY.category == ErrorCategory.CONFIGURATION
    assert ErrorCode.TOKEN_ACQUISITION_FAILED.category == ErrorCategory.AUTHENTICATION
    assert ErrorCode.NETWORK_TIMEOUT.category == ErrorCategory.NETWORK


def test_plugin_error_with_code() -> None:
    """Test PluginError includes error code and troubleshooting."""
    error = ConfigurationError(
        ErrorCode.CONFIG_MISSING_KEY,
        "Missing 'ClientId' in configuration",
        details={"server": "test-server", "missing_key": "ClientId"},
    )

    assert error.error_code == ErrorCode.CONFIG_MISSING_KEY
    assert error.http_status == 500
    assert "ClientId" in error.message
    assert error.details["server"] == "test-server"
    assert len(error.troubleshooting_steps) > 0
    assert error.documentation_url is not None


def test_error_to_dict() -> None:
    """Test error serialization for API responses."""
    error = NetworkError(
        ErrorCode.NETWORK_TIMEOUT,
        "Connection timeout to token endpoint",
        details={"endpoint": "https://login.example.com/token", "timeout": 30},
    )

    error_dict = error.to_dict()

    assert error_dict["error_code"] == "NET-001"
    assert error_dict["category"] == "NETWORK"
    assert error_dict["severity"] == "ERROR"
    assert error_dict["message"] == "Connection timeout to token endpoint"
    assert "troubleshooting" in error_dict
    assert "documentation_url" in error_dict
    assert error_dict["details"]["endpoint"] == "https://login.example.com/token"


def test_error_severity_levels() -> None:
    """Test different severity levels."""
    warning = PluginError(
        ErrorCode.TOKEN_REFRESH_RECOMMENDED,
        "Token expiring soon",
        severity=ErrorSeverity.WARNING,
    )

    critical = PluginError(
        ErrorCode.AUTH_PROVIDER_UNAVAILABLE,
        "Cannot reach authentication provider",
        severity=ErrorSeverity.CRITICAL,
    )

    assert warning.severity == ErrorSeverity.WARNING
    assert warning.http_status == 200
    assert critical.severity == ErrorSeverity.CRITICAL
    assert critical.http_status == 503
