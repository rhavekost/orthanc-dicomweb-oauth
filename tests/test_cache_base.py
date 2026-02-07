"""Tests for cache abstraction interface."""
import pytest

from src.cache.base import CacheBackend


def test_cache_backend_is_abstract() -> None:
    """Test that CacheBackend cannot be instantiated directly."""
    with pytest.raises(TypeError):
        CacheBackend()  # type: ignore[abstract]


def test_cache_backend_defines_interface() -> None:
    """Test that CacheBackend defines required methods."""
    required_methods = ["get", "set", "delete", "exists", "clear"]
    for method in required_methods:
        assert hasattr(CacheBackend, method)
