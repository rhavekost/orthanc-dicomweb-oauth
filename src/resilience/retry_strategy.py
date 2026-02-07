"""Configurable retry strategies with various backoff algorithms."""
import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class RetryExhaustedError(Exception):
    """Raised when all retry attempts are exhausted."""

    pass


class RetryStrategy(ABC):
    """Abstract base class for retry strategies."""

    @abstractmethod
    def get_delay(self, attempt: int) -> float:
        """
        Calculate delay for given attempt number.

        Args:
            attempt: Current attempt number (0-indexed)

        Returns:
            Delay in seconds before next retry
        """
        pass


class FixedBackoff(RetryStrategy):
    """Fixed delay between retries."""

    def __init__(self, delay: float):
        """
        Initialize fixed backoff.

        Args:
            delay: Fixed delay in seconds
        """
        self.delay = delay

    def get_delay(self, attempt: int) -> float:
        """Return fixed delay regardless of attempt."""
        return self.delay


class LinearBackoff(RetryStrategy):
    """Linear increase in delay between retries."""

    def __init__(self, initial_delay: float, increment: float):
        """
        Initialize linear backoff.

        Args:
            initial_delay: Initial delay in seconds
            increment: Amount to increase delay each attempt
        """
        self.initial_delay = initial_delay
        self.increment = increment

    def get_delay(self, attempt: int) -> float:
        """Return linearly increasing delay."""
        return self.initial_delay + (attempt * self.increment)


class ExponentialBackoff(RetryStrategy):
    """Exponential increase in delay between retries."""

    def __init__(
        self,
        initial_delay: float,
        multiplier: float = 2.0,
        max_delay: Optional[float] = None,
    ):
        """
        Initialize exponential backoff.

        Args:
            initial_delay: Initial delay in seconds
            multiplier: Factor to multiply delay each attempt
            max_delay: Maximum delay cap (optional)
        """
        self.initial_delay = initial_delay
        self.multiplier = multiplier
        self.max_delay = max_delay

    def get_delay(self, attempt: int) -> float:
        """Return exponentially increasing delay."""
        delay = self.initial_delay * (self.multiplier**attempt)

        if self.max_delay is not None:
            delay = min(delay, self.max_delay)

        return delay


class RetryConfig:
    """Configuration for retry behavior with strategy pattern."""

    def __init__(
        self,
        max_attempts: int,
        strategy: RetryStrategy,
        should_retry: Optional[Callable[[Exception], bool]] = None,
        on_retry: Optional[Callable[[int, Exception], None]] = None,
    ):
        """
        Initialize retry configuration.

        Args:
            max_attempts: Maximum number of attempts
            strategy: Retry strategy for calculating delays
            should_retry: Optional function to determine if exception
                should trigger retry
            on_retry: Optional callback before each retry
        """
        self.max_attempts = max_attempts
        self.strategy = strategy
        self.should_retry = should_retry or (lambda e: True)
        self.on_retry = on_retry

    def execute(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """
        Execute function with retry logic.

        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result

        Raises:
            RetryExhaustedError: If all attempts fail
            Exception: If exception is not retryable
        """
        last_exception: Optional[Exception] = None

        for attempt in range(self.max_attempts):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e

                # Check if we should retry this exception
                if not self.should_retry(e):
                    raise

                # Check if we have attempts remaining
                if attempt >= self.max_attempts - 1:
                    break

                # Call retry callback if provided
                if self.on_retry:
                    self.on_retry(attempt, e)

                # Calculate and apply delay
                delay = self.strategy.get_delay(attempt)
                logger.debug(
                    f"Retry attempt {attempt + 1}/{self.max_attempts} "
                    f"after {delay}s delay"
                )
                time.sleep(delay)

        # All attempts exhausted
        raise RetryExhaustedError(
            f"Operation failed after {self.max_attempts} attempts: " f"{last_exception}"
        ) from last_exception
