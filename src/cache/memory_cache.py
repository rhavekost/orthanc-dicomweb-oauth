"""In-memory cache implementation."""
import threading
import time
from typing import Any, Dict, Optional, Tuple

from src.cache.base import CacheBackend


class MemoryCache(CacheBackend):
    """Thread-safe in-memory cache implementation.

    This is the default cache backend for single-instance deployments.
    Stores data in a Python dictionary with thread-safe operations.
    """

    def __init__(self) -> None:
        """Initialize the memory cache."""
        self._cache: Dict[str, Tuple[Any, Optional[float]]] = {}
        self._lock = threading.RLock()

    def get(self, key: str) -> Optional[Any]:
        """Retrieve a value from the cache."""
        with self._lock:
            if key not in self._cache:
                return None

            value, expiry = self._cache[key]

            # Check expiration
            if expiry is not None and time.time() > expiry:
                del self._cache[key]
                return None

            return value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Store a value in the cache."""
        with self._lock:
            expiry = None
            if ttl is not None:
                expiry = time.time() + ttl

            self._cache[key] = (value, expiry)
            return True

    def delete(self, key: str) -> bool:
        """Delete a value from the cache."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def exists(self, key: str) -> bool:
        """Check if a key exists in the cache."""
        return self.get(key) is not None

    def clear(self) -> bool:
        """Clear all entries from the cache."""
        with self._lock:
            self._cache.clear()
            return True
