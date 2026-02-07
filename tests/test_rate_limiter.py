"""Tests for rate limiting."""
import time

import pytest

from src.rate_limiter import RateLimiter, RateLimitExceeded


def test_rate_limiter_allows_within_limit() -> None:
    """Test that rate limiter allows requests within limit."""
    limiter = RateLimiter(max_requests=5, window_seconds=1)

    # Should allow 5 requests
    for i in range(5):
        limiter.check_rate_limit("test-key")

    # No exception should be raised


def test_rate_limiter_blocks_over_limit() -> None:
    """Test that rate limiter blocks requests over limit."""
    limiter = RateLimiter(max_requests=3, window_seconds=1)

    # Allow 3 requests
    for i in range(3):
        limiter.check_rate_limit("test-key")

    # 4th request should be blocked
    with pytest.raises(RateLimitExceeded):
        limiter.check_rate_limit("test-key")


def test_rate_limiter_resets_after_window() -> None:
    """Test that rate limiter resets after time window."""
    limiter = RateLimiter(max_requests=2, window_seconds=0.5)

    # Use 2 requests
    limiter.check_rate_limit("test-key")
    limiter.check_rate_limit("test-key")

    # Should be blocked
    with pytest.raises(RateLimitExceeded):
        limiter.check_rate_limit("test-key")

    # Wait for window to expire
    time.sleep(0.6)

    # Should be allowed again
    limiter.check_rate_limit("test-key")


def test_rate_limiter_per_key() -> None:
    """Test that rate limiter tracks requests per key."""
    limiter = RateLimiter(max_requests=2, window_seconds=1)

    # Use limit for key1
    limiter.check_rate_limit("key1")
    limiter.check_rate_limit("key1")

    # key1 should be blocked
    with pytest.raises(RateLimitExceeded):
        limiter.check_rate_limit("key1")

    # key2 should still be allowed
    limiter.check_rate_limit("key2")
    limiter.check_rate_limit("key2")


def test_rate_limit_exceeded_details() -> None:
    """Test that RateLimitExceeded contains useful details."""
    limiter = RateLimiter(max_requests=1, window_seconds=1)

    limiter.check_rate_limit("test-key")

    try:
        limiter.check_rate_limit("test-key")
        assert False, "Should have raised RateLimitExceeded"
    except RateLimitExceeded as e:
        assert "test-key" in str(e)
        assert "1" in str(e)  # max_requests
