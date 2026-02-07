"""Tests for secret redaction in logs."""
import json
from io import StringIO

from src.structured_logger import StructuredLogger, redact_secrets


def test_redact_secrets_in_string():
    """Test secret redaction in plain strings."""
    # Test various secret patterns
    test_cases = [
        (
            "client_secret=abc123xyz",
            "client_secret=***REDACTED***",
        ),
        (
            "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test",
            "Bearer ***REDACTED***",
        ),
        (
            "Authorization: Bearer token123",
            "Authorization: Bearer ***REDACTED***",
        ),
        (
            "password: my_secret_pass",
            "password: ***REDACTED***",
        ),
        (
            "api_key=sk_live_123456",
            "api_key=***REDACTED***",
        ),
    ]

    for original, expected in test_cases:
        result = redact_secrets(original)
        assert result == expected, f"Failed for: {original}"


def test_redact_secrets_in_dict():
    """Test secret redaction in dictionaries."""
    data = {
        "client_id": "public_client",
        "client_secret": "super_secret_123",
        "access_token": "eyJhbGci...",
        "username": "test_user",
        "password": "my_password",
    }

    redacted = redact_secrets(data)

    assert redacted["client_id"] == "public_client"  # Not redacted
    assert redacted["client_secret"] == "***REDACTED***"
    assert redacted["access_token"] == "***REDACTED***"
    assert redacted["username"] == "test_user"  # Not redacted
    assert redacted["password"] == "***REDACTED***"


def test_structured_logger_redacts_secrets():
    """Test that structured logger redacts secrets automatically."""
    stream = StringIO()
    logger = StructuredLogger(name="test-redact")
    logger.logger.handlers[0].stream = stream

    # Log entry with secrets
    logger.error(
        "Token acquisition failed",
        error="Invalid client_secret=abc123xyz",
        token="Bearer eyJhbGci...",
    )

    # Parse log output
    log_output = stream.getvalue()
    log_entry = json.loads(log_output.strip())

    # Secrets should be redacted
    assert "client_secret=***REDACTED***" in log_entry["error"]
    assert log_entry["token"] == "***REDACTED***"
    assert "abc123xyz" not in log_output
    assert "eyJhbGci" not in log_output
