"""Tests for Redis cache implementation."""
from typing import Any, Generator
from unittest.mock import MagicMock, patch

import pytest

from src.cache.redis_cache import RedisCache


@pytest.fixture  # type: ignore[misc]
def mock_redis() -> Generator[MagicMock, None, None]:
    """Create a mock Redis client."""
    with patch("src.cache.redis_cache.redis.Redis") as mock:
        redis_client = MagicMock()
        mock.return_value = redis_client
        yield redis_client


def test_redis_cache_initialization(mock_redis: Any) -> None:
    """Test Redis cache initialization."""
    cache = RedisCache(host="localhost", port=6379, db=0)
    assert cache is not None


def test_redis_cache_set_and_get(mock_redis: Any) -> None:
    """Test basic set and get operations."""
    mock_redis.get.return_value = b'"value1"'
    mock_redis.set.return_value = True

    cache = RedisCache(host="localhost", port=6379)
    assert cache.set("key1", "value1") is True

    result = cache.get("key1")
    assert result == "value1"


def test_redis_cache_get_nonexistent(mock_redis: Any) -> None:
    """Test getting a non-existent key returns None."""
    mock_redis.get.return_value = None

    cache = RedisCache(host="localhost", port=6379)
    assert cache.get("nonexistent") is None


def test_redis_cache_set_with_ttl(mock_redis: Any) -> None:
    """Test setting value with TTL."""
    mock_redis.setex.return_value = True

    cache = RedisCache(host="localhost", port=6379)
    assert cache.set("key1", "value1", ttl=300) is True

    mock_redis.setex.assert_called_once()


def test_redis_cache_exists(mock_redis: Any) -> None:
    """Test exists method."""
    mock_redis.exists.return_value = 1

    cache = RedisCache(host="localhost", port=6379)
    assert cache.exists("key1") is True

    mock_redis.exists.return_value = 0
    assert cache.exists("nonexistent") is False


def test_redis_cache_delete(mock_redis: Any) -> None:
    """Test delete operation."""
    mock_redis.delete.return_value = 1

    cache = RedisCache(host="localhost", port=6379)
    assert cache.delete("key1") is True

    mock_redis.delete.return_value = 0
    assert cache.delete("nonexistent") is False


def test_redis_cache_clear(mock_redis: Any) -> None:
    """Test clearing all entries."""
    mock_redis.flushdb.return_value = True

    cache = RedisCache(host="localhost", port=6379)
    assert cache.clear() is True


def test_redis_cache_connection_failure() -> None:
    """Test handling of Redis connection failures."""
    with patch("src.cache.redis_cache.redis.Redis") as mock:
        mock.side_effect = Exception("Connection refused")

        with pytest.raises(Exception):
            RedisCache(host="localhost", port=6379)


def test_redis_cache_serialization(mock_redis: Any) -> None:
    """Test JSON serialization of complex objects."""
    mock_redis.set.return_value = True
    mock_redis.get.return_value = b'{"key": "value", "number": 42}'

    cache = RedisCache(host="localhost", port=6379)

    # Set complex object
    data = {"key": "value", "number": 42}
    assert cache.set("complex", data) is True

    # Get and verify
    result = cache.get("complex")
    assert result == data
