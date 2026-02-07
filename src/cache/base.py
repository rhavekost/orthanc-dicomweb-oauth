"""Abstract base class for cache backends."""
from abc import ABC, abstractmethod
from typing import Any, Optional


class CacheBackend(ABC):
    """Abstract interface for cache backends.

    Provides a common interface for different cache implementations
    (in-memory, Redis, Memcached, etc.) to enable distributed caching
    for multi-instance deployments.
    """

    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Retrieve a value from the cache.

        Args:
            key: The cache key

        Returns:
            The cached value, or None if not found or expired
        """
        pass

    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Store a value in the cache.

        Args:
            key: The cache key
            value: The value to cache
            ttl: Time-to-live in seconds (None = no expiration)

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete a value from the cache.

        Args:
            key: The cache key

        Returns:
            True if key existed and was deleted, False otherwise
        """
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if a key exists in the cache.

        Args:
            key: The cache key

        Returns:
            True if key exists and has not expired, False otherwise
        """
        pass

    @abstractmethod
    def clear(self) -> bool:
        """Clear all entries from the cache.

        Returns:
            True if successful, False otherwise
        """
        pass
