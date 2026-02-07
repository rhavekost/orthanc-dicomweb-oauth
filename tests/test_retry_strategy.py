"""Tests for retry strategy patterns."""
import time

import pytest

from src.resilience.retry_strategy import (
    ExponentialBackoff,
    FixedBackoff,
    LinearBackoff,
    RetryConfig,
    RetryExhaustedError,
)


def test_fixed_backoff_delays() -> None:
    """Test fixed backoff calculates constant delays."""
    strategy = FixedBackoff(delay=1.0)

    assert strategy.get_delay(0) == 1.0
    assert strategy.get_delay(1) == 1.0
    assert strategy.get_delay(5) == 1.0


def test_linear_backoff_delays() -> None:
    """Test linear backoff increases linearly."""
    strategy = LinearBackoff(initial_delay=1.0, increment=0.5)

    assert strategy.get_delay(0) == 1.0
    assert strategy.get_delay(1) == 1.5
    assert strategy.get_delay(2) == 2.0
    assert strategy.get_delay(3) == 2.5


def test_exponential_backoff_delays() -> None:
    """Test exponential backoff doubles delay."""
    strategy = ExponentialBackoff(initial_delay=1.0, multiplier=2.0)

    assert strategy.get_delay(0) == 1.0
    assert strategy.get_delay(1) == 2.0
    assert strategy.get_delay(2) == 4.0
    assert strategy.get_delay(3) == 8.0


def test_exponential_backoff_with_max_delay() -> None:
    """Test exponential backoff respects max delay."""
    strategy = ExponentialBackoff(initial_delay=1.0, multiplier=2.0, max_delay=5.0)

    assert strategy.get_delay(0) == 1.0
    assert strategy.get_delay(1) == 2.0
    assert strategy.get_delay(2) == 4.0
    assert strategy.get_delay(3) == 5.0  # Capped
    assert strategy.get_delay(4) == 5.0  # Still capped


def test_retry_config_max_attempts() -> None:
    """Test retry config respects max attempts."""
    config = RetryConfig(max_attempts=3, strategy=FixedBackoff(delay=0.01))

    call_count = 0

    def failing_operation() -> None:
        nonlocal call_count
        call_count += 1
        raise Exception("Always fails")

    with pytest.raises(RetryExhaustedError) as exc_info:
        config.execute(failing_operation)

    assert call_count == 3
    assert "after 3 attempts" in str(exc_info.value)


def test_retry_config_success_on_retry() -> None:
    """Test retry config succeeds after failures."""
    config = RetryConfig(max_attempts=3, strategy=FixedBackoff(delay=0.01))

    call_count = 0

    def operation_succeeds_on_second_try() -> str:
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise Exception("Not yet")
        return "success"

    result = config.execute(operation_succeeds_on_second_try)

    assert result == "success"
    assert call_count == 2


def test_retry_config_with_exception_filter() -> None:
    """Test retry only on specific exceptions."""

    class RetryableError(Exception):
        pass

    class NonRetryableError(Exception):
        pass

    config = RetryConfig(
        max_attempts=3,
        strategy=FixedBackoff(delay=0.01),
        should_retry=lambda e: isinstance(e, RetryableError),
    )

    # Non-retryable exception should fail immediately
    def non_retryable_op() -> None:
        raise NonRetryableError("Immediate")

    with pytest.raises(NonRetryableError):
        config.execute(non_retryable_op)

    # Retryable exception should retry
    call_count = 0

    def retryable_operation() -> str:
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise RetryableError("Retry me")
        return "success"

    result = config.execute(retryable_operation)
    assert result == "success"
    assert call_count == 2


def test_retry_config_timing() -> None:
    """Test retry config respects backoff timing."""
    config = RetryConfig(max_attempts=3, strategy=FixedBackoff(delay=0.1))

    call_count = 0
    start_time = time.time()

    def failing_operation() -> None:
        nonlocal call_count
        call_count += 1
        raise Exception("Always fails")

    with pytest.raises(RetryExhaustedError):
        config.execute(failing_operation)

    elapsed = time.time() - start_time

    # Should have 2 delays (between 3 attempts) of 0.1s each
    assert elapsed >= 0.2
    assert call_count == 3


def test_retry_config_callback() -> None:
    """Test retry config calls callback on each attempt."""
    attempts_log: list[tuple[int, str]] = []

    def on_retry(attempt: int, exception: Exception) -> None:
        attempts_log.append((attempt, str(exception)))

    config = RetryConfig(
        max_attempts=3, strategy=FixedBackoff(delay=0.01), on_retry=on_retry
    )

    def failing_operation() -> None:
        raise ValueError("Test error")

    with pytest.raises(RetryExhaustedError):
        config.execute(failing_operation)

    assert len(attempts_log) == 2  # Callbacks before 2nd and 3rd attempts
    assert attempts_log[0][0] == 0
    assert "Test error" in attempts_log[0][1]
