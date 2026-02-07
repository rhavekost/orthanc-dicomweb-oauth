"""Tests for in-memory cache implementation."""
import threading
import time

from src.cache.memory_cache import MemoryCache


def test_memory_cache_set_and_get() -> None:
    """Test basic set and get operations."""
    cache = MemoryCache()
    assert cache.set("key1", "value1") is True
    assert cache.get("key1") == "value1"


def test_memory_cache_get_nonexistent() -> None:
    """Test getting a non-existent key returns None."""
    cache = MemoryCache()
    assert cache.get("nonexistent") is None


def test_memory_cache_ttl_expiration() -> None:
    """Test that values expire after TTL."""
    cache = MemoryCache()
    cache.set("key1", "value1", ttl=1)
    assert cache.get("key1") == "value1"
    time.sleep(1.1)
    assert cache.get("key1") is None


def test_memory_cache_exists() -> None:
    """Test exists method."""
    cache = MemoryCache()
    cache.set("key1", "value1")
    assert cache.exists("key1") is True
    assert cache.exists("nonexistent") is False


def test_memory_cache_delete() -> None:
    """Test delete operation."""
    cache = MemoryCache()
    cache.set("key1", "value1")
    assert cache.delete("key1") is True
    assert cache.get("key1") is None
    assert cache.delete("nonexistent") is False


def test_memory_cache_clear() -> None:
    """Test clearing all entries."""
    cache = MemoryCache()
    cache.set("key1", "value1")
    cache.set("key2", "value2")
    assert cache.clear() is True
    assert cache.get("key1") is None
    assert cache.get("key2") is None


def test_memory_cache_thread_safety() -> None:
    """Test thread-safe operations."""
    cache = MemoryCache()

    def writer(key_num: int) -> None:
        for i in range(100):
            cache.set(f"key_{key_num}_{i}", f"value_{i}")

    threads = [threading.Thread(target=writer, args=(i,)) for i in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Verify no crashes and data integrity
    assert cache.exists("key_0_0") is True
