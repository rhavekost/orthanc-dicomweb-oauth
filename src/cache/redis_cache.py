"""Redis cache implementation."""
import json
from typing import Any, Optional

import redis  # noqa: TCH002

from src.cache.base import CacheBackend


class RedisCache(CacheBackend):
    """Redis-based distributed cache implementation.

    This cache backend enables token sharing across multiple instances
    of the plugin, improving performance and reducing load on OAuth providers.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        prefix: str = "orthanc:oauth:",
    ):
        """Initialize the Redis cache.

        Args:
            host: Redis server hostname
            port: Redis server port
            db: Redis database number
            password: Redis password (optional)
            prefix: Key prefix for namespacing
        """
        self._prefix = prefix
        self._client = redis.Redis(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=False,  # We'll handle encoding
        )

        # Test connection
        self._client.ping()

    def _make_key(self, key: str) -> str:
        """Add prefix to key for namespacing."""
        return f"{self._prefix}{key}"

    def get(self, key: str) -> Optional[Any]:
        """Retrieve a value from the cache."""
        try:
            value = self._client.get(self._make_key(key))
            if value is None:
                return None

            # Deserialize JSON
            return json.loads(value.decode("utf-8"))
        except Exception:
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Store a value in the cache."""
        try:
            # Serialize to JSON
            serialized = json.dumps(value).encode("utf-8")

            if ttl is not None:
                return bool(self._client.setex(self._make_key(key), ttl, serialized))
            else:
                return bool(self._client.set(self._make_key(key), serialized))
        except Exception:
            return False

    def delete(self, key: str) -> bool:
        """Delete a value from the cache."""
        try:
            return bool(self._client.delete(self._make_key(key)))
        except Exception:
            return False

    def exists(self, key: str) -> bool:
        """Check if a key exists in the cache."""
        try:
            return bool(self._client.exists(self._make_key(key)))
        except Exception:
            return False

    def clear(self) -> bool:
        """Clear all entries from the cache.

        WARNING: This flushes the entire Redis database.
        Use with caution in shared Redis environments.
        """
        try:
            return bool(self._client.flushdb())
        except Exception:
            return False
