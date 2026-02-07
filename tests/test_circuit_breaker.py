"""Tests for circuit breaker pattern."""
import time

import pytest

from src.resilience.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerError,
    CircuitBreakerState,
)


def test_circuit_breaker_success() -> None:
    """Test circuit breaker in closed state with successful calls."""
    cb = CircuitBreaker(failure_threshold=3, timeout=1)

    def successful_operation() -> str:
        return "success"

    result = cb.call(successful_operation)
    assert result == "success"
    assert cb.state == CircuitBreakerState.CLOSED
    assert cb.failure_count == 0


def test_circuit_breaker_opens_on_failures() -> None:
    """Test circuit breaker opens after failure threshold."""
    cb = CircuitBreaker(failure_threshold=3, timeout=1)

    def failing_operation() -> None:
        raise Exception("Service unavailable")

    # First 2 failures should keep circuit closed
    for i in range(2):
        with pytest.raises(Exception):
            cb.call(failing_operation)
        assert cb.state == CircuitBreakerState.CLOSED

    # 3rd failure should open circuit
    with pytest.raises(Exception):
        cb.call(failing_operation)
    assert cb.state == CircuitBreakerState.OPEN
    assert cb.failure_count == 3


def test_circuit_breaker_rejects_calls_when_open() -> None:
    """Test circuit breaker rejects calls in open state."""
    cb = CircuitBreaker(failure_threshold=2, timeout=1)

    def failing_operation() -> None:
        raise Exception("Service unavailable")

    # Trigger failures to open circuit
    for _ in range(2):
        with pytest.raises(Exception):
            cb.call(failing_operation)

    assert cb.state == CircuitBreakerState.OPEN

    # Next call should be rejected immediately
    with pytest.raises(CircuitBreakerError) as exc_info:
        cb.call(failing_operation)

    assert "Circuit breaker is OPEN" in str(exc_info.value)


def test_circuit_breaker_half_open_after_timeout() -> None:
    """Test circuit breaker transitions to half-open after timeout."""
    cb = CircuitBreaker(failure_threshold=2, timeout=0.1)

    def failing_operation() -> None:
        raise Exception("Service unavailable")

    # Open the circuit
    for _ in range(2):
        with pytest.raises(Exception):
            cb.call(failing_operation)

    assert cb.state == CircuitBreakerState.OPEN

    # Wait for timeout
    time.sleep(0.15)

    # Next call should transition to half-open
    def successful_operation() -> str:
        return "success"

    result = cb.call(successful_operation)
    assert result == "success"
    assert cb.state == CircuitBreakerState.CLOSED  # type: ignore[comparison-overlap]


def test_circuit_breaker_resets_on_success() -> None:
    """Test circuit breaker resets failure count on success."""
    cb = CircuitBreaker(failure_threshold=3, timeout=1)

    def failing_operation() -> None:
        raise Exception("Service unavailable")

    def successful_operation() -> str:
        return "success"

    # 2 failures
    for _ in range(2):
        with pytest.raises(Exception):
            cb.call(failing_operation)

    assert cb.failure_count == 2

    # Success should reset counter
    cb.call(successful_operation)
    assert cb.failure_count == 0
    assert cb.state == CircuitBreakerState.CLOSED


def test_circuit_breaker_with_custom_exception_filter() -> None:
    """Test circuit breaker with exception filter."""

    class NetworkError(Exception):
        pass

    class ValidationError(Exception):
        pass

    cb = CircuitBreaker(
        failure_threshold=2,
        timeout=1,
        exception_filter=lambda e: isinstance(e, NetworkError),
    )

    def operation_with_network_error() -> None:
        raise NetworkError("Connection failed")

    def operation_with_validation_error() -> None:
        raise ValidationError("Invalid input")

    # ValidationError shouldn't count toward failures
    with pytest.raises(ValidationError):
        cb.call(operation_with_validation_error)

    assert cb.failure_count == 0

    # NetworkError should count
    with pytest.raises(NetworkError):
        cb.call(operation_with_network_error)

    assert cb.failure_count == 1


def test_circuit_breaker_metrics() -> None:
    """Test circuit breaker exposes metrics."""
    cb = CircuitBreaker(failure_threshold=3, timeout=1)

    def operation() -> str:
        return "success"

    # Execute some calls
    for _ in range(5):
        cb.call(operation)

    metrics = cb.get_metrics()

    assert metrics["state"] == "CLOSED"
    assert metrics["failure_count"] == 0
    assert metrics["total_calls"] == 5
    assert metrics["success_count"] == 5
    assert metrics["failure_threshold"] == 3
