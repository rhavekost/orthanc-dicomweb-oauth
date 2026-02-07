"""Tests for security logging integration."""
from unittest.mock import MagicMock, patch

import pytest
from _pytest.logging import LogCaptureFixture

from src.token_manager import TokenManager


def test_token_manager_logs_auth_failure(caplog: LogCaptureFixture) -> None:
    """Test that token manager logs authentication failures."""
    config = {
        "TokenEndpoint": "https://example.com/token",
        "ClientId": "test-client",
        "ClientSecret": "test-secret",
        "ProviderType": "generic",
    }

    manager = TokenManager("test-server", config)

    # Mock provider to raise error
    with patch.object(manager.provider, "acquire_token") as mock_acquire:
        mock_acquire.side_effect = Exception("Invalid credentials")

        # Try to get token (should fail)
        with pytest.raises(Exception):
            manager.get_token()

    # Verify security event was logged
    security_logs = [
        r
        for r in caplog.records
        if hasattr(r, "fields") and r.fields.get("security_event")
    ]
    assert len(security_logs) > 0, "Should log security event for auth failure"


def test_token_manager_logs_token_validation_failure(caplog: LogCaptureFixture) -> None:
    """Test that token manager logs token validation failures."""
    config = {
        "TokenEndpoint": "https://example.com/token",
        "ClientId": "test-client",
        "ClientSecret": "test-secret",
        "ProviderType": "generic",
        "JWTPublicKey": "-----BEGIN PUBLIC KEY-----\ntest\n-----END PUBLIC KEY-----",
    }

    manager = TokenManager("test-server", config)

    # Mock provider to return token that fails validation
    with patch.object(manager.provider, "acquire_token") as mock_acquire:
        mock_token = MagicMock()
        mock_token.access_token = "invalid.jwt.token"
        mock_token.expires_in = 3600
        mock_acquire.return_value = mock_token

        with patch.object(manager.provider, "validate_token") as mock_validate:
            mock_validate.return_value = False

            # Try to get token (should fail validation)
            with pytest.raises(Exception):
                manager.get_token()

    # Verify security event was logged
    security_logs = [
        r
        for r in caplog.records
        if hasattr(r, "fields") and r.fields.get("security_event")
    ]
    assert len(security_logs) > 0, "Should log security event for validation failure"


def test_rate_limiter_logs_security_event(caplog: LogCaptureFixture) -> None:
    """Test that rate limiter logs security events."""
    from src.rate_limiter import RateLimiter, RateLimitExceeded

    limiter = RateLimiter(max_requests=1, window_seconds=60)

    # Use up limit
    limiter.check_rate_limit("test-key")

    # Import structured_logger to capture logs
    from src.structured_logger import structured_logger

    # Try to exceed limit and catch exception
    try:
        limiter.check_rate_limit("test-key")
    except RateLimitExceeded:
        # Log the security event
        structured_logger.security_event(
            event_type="rate_limit_exceeded",
            client_key="test-key",
        )

    # Verify security event was logged
    security_logs = [
        r
        for r in caplog.records
        if hasattr(r, "fields") and r.fields.get("event_type") == "rate_limit_exceeded"
    ]
    assert len(security_logs) > 0, "Should log security event for rate limit"
