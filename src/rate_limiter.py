"""Rate limiting for API endpoints."""
import threading
import time
from collections import defaultdict, deque
from typing import DefaultDict, Deque


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded."""

    def __init__(self, key: str, max_requests: int, window_seconds: float):
        """
        Initialize rate limit exception.

        Args:
            key: Rate limit key that exceeded limit
            max_requests: Maximum requests allowed
            window_seconds: Time window in seconds
        """
        self.key = key
        self.max_requests = max_requests
        self.window_seconds = window_seconds

        super().__init__(
            f"Rate limit exceeded for '{key}': "
            f"{max_requests} requests per {window_seconds}s"
        )


class RateLimiter:
    """
    Token bucket rate limiter.

    Tracks requests per key (e.g., IP address, server name) within a
    sliding time window.

    Thread-safe for concurrent use.

    Example:
        >>> limiter = RateLimiter(max_requests=10, window_seconds=60)
        >>> limiter.check_rate_limit(client_ip)  # Raises if over limit
    """

    def __init__(self, max_requests: int, window_seconds: float) -> None:
        """
        Initialize rate limiter.

        Args:
            max_requests: Maximum requests allowed per window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds

        # Track request timestamps per key
        self._requests: DefaultDict[str, Deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def check_rate_limit(self, key: str) -> None:
        """
        Check if request is within rate limit.

        Args:
            key: Rate limit key (e.g., IP address, server name)

        Raises:
            RateLimitExceeded: If rate limit exceeded for this key
        """
        with self._lock:
            now = time.time()
            cutoff = now - self.window_seconds

            # Get request history for this key
            requests = self._requests[key]

            # Remove old requests outside the window
            while requests and requests[0] < cutoff:
                requests.popleft()

            # Check if limit exceeded
            if len(requests) >= self.max_requests:
                raise RateLimitExceeded(key, self.max_requests, self.window_seconds)

            # Record this request
            requests.append(now)

    def reset(self, key: str) -> None:
        """
        Reset rate limit for a key.

        Args:
            key: Rate limit key to reset
        """
        with self._lock:
            if key in self._requests:
                del self._requests[key]

    def get_remaining(self, key: str) -> int:
        """
        Get remaining requests for a key.

        Args:
            key: Rate limit key

        Returns:
            Number of requests remaining in current window
        """
        with self._lock:
            now = time.time()
            cutoff = now - self.window_seconds

            requests = self._requests[key]

            # Remove old requests
            while requests and requests[0] < cutoff:
                requests.popleft()

            return max(0, self.max_requests - len(requests))
