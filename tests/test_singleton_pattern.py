"""Tests for singleton pattern implementation."""
import threading

import pytest

from src.plugin_context import PluginContext


def test_singleton_instance() -> None:
    """Test that PluginContext is a singleton."""
    instance1 = PluginContext.get_instance()
    instance2 = PluginContext.get_instance()

    assert instance1 is instance2


def test_singleton_initialization() -> None:
    """Test singleton can be initialized only once."""
    # Reset singleton for test
    PluginContext._instance = None
    PluginContext._initialized = False

    instance1 = PluginContext.get_instance()
    instance1.register_token_manager("test-server", "manager", "http://test.com")

    instance2 = PluginContext.get_instance()
    assert instance2.get_token_manager("test-server") is not None


def test_singleton_thread_safety() -> None:
    """Test that singleton is thread-safe."""
    instances = []

    def create_instance() -> None:
        instance = PluginContext.get_instance()
        instances.append(id(instance))

    # Reset singleton
    PluginContext._instance = None
    PluginContext._initialized = False

    # Create 10 threads trying to get instance simultaneously
    threads = [threading.Thread(target=create_instance) for _ in range(10)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    # All should have same instance ID
    assert len(set(instances)) == 1


def test_singleton_reset() -> None:
    """Test singleton can be reset for testing."""
    instance1 = PluginContext.get_instance()
    instance1.register_token_manager("test1", "manager1", "http://test1.com")

    # Reset
    PluginContext.reset_instance()

    instance2 = PluginContext.get_instance()
    assert instance1 is not instance2
    assert instance2.get_token_manager("test1") is None


def test_no_direct_instantiation() -> None:
    """Test that PluginContext cannot be directly instantiated."""
    with pytest.raises(RuntimeError) as exc_info:
        PluginContext()

    assert "Use get_instance()" in str(exc_info.value)
