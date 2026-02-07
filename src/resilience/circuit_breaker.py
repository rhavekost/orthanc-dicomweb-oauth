"""Circuit breaker pattern implementation."""
import logging
import threading
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


class CircuitBreakerState(str, Enum):
    """Circuit breaker states."""

    CLOSED = "CLOSED"  # Normal operation
    OPEN = "OPEN"  # Failing, reject calls
    HALF_OPEN = "HALF_OPEN"  # Testing recovery


class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open."""

    pass


@dataclass
class CircuitBreakerMetrics:
    """Metrics for circuit breaker."""

    total_calls: int = 0
    success_count: int = 0
    failure_count: int = 0
    rejected_count: int = 0


class CircuitBreaker:
    """
    Circuit breaker pattern for fault tolerance.

    Prevents cascading failures by opening circuit after threshold failures.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: float = 60.0,
        exception_filter: Optional[Callable[[Exception], bool]] = None,
    ):
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            timeout: Seconds before attempting to close circuit (half-open)
            exception_filter: Optional function to filter which exceptions
                count as failures
        """
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.exception_filter = exception_filter or (lambda e: True)

        self._state = CircuitBreakerState.CLOSED
        self._failure_count = 0
        self._last_failure_time: Optional[float] = None
        self._lock = threading.Lock()

        # Metrics
        self._metrics = CircuitBreakerMetrics()

    @property
    def state(self) -> CircuitBreakerState:
        """Get current circuit breaker state."""
        with self._lock:
            return self._state

    @property
    def failure_count(self) -> int:
        """Get current failure count."""
        with self._lock:
            return self._failure_count

    def call(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """
        Execute function with circuit breaker protection.

        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result

        Raises:
            CircuitBreakerError: If circuit is open
            Exception: Original exception from func
        """
        with self._lock:
            self._metrics.total_calls += 1

            # Check if we should transition from OPEN to HALF_OPEN
            if self._state == CircuitBreakerState.OPEN:
                if self._should_attempt_reset():
                    self._state = CircuitBreakerState.HALF_OPEN
                    logger.info("Circuit breaker entering HALF_OPEN state")
                else:
                    self._metrics.rejected_count += 1
                    raise CircuitBreakerError(
                        f"Circuit breaker is OPEN (failures: {self._failure_count})"
                    )

        # Execute the function
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            if self.exception_filter(e):
                self._on_failure()
            raise

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if self._last_failure_time is None:
            return True
        return time.time() - self._last_failure_time >= self.timeout

    def _on_success(self) -> None:
        """Handle successful call."""
        with self._lock:
            self._metrics.success_count += 1
            self._failure_count = 0

            if self._state == CircuitBreakerState.HALF_OPEN:
                self._state = CircuitBreakerState.CLOSED
                logger.info("Circuit breaker CLOSED after successful call")

    def _on_failure(self) -> None:
        """Handle failed call."""
        with self._lock:
            self._metrics.failure_count += 1
            self._failure_count += 1
            self._last_failure_time = time.time()

            if self._failure_count >= self.failure_threshold:
                if self._state != CircuitBreakerState.OPEN:
                    self._state = CircuitBreakerState.OPEN
                    logger.warning(
                        f"Circuit breaker OPENED after {self._failure_count} failures"
                    )

    def reset(self) -> None:
        """Manually reset circuit breaker to closed state."""
        with self._lock:
            self._state = CircuitBreakerState.CLOSED
            self._failure_count = 0
            self._last_failure_time = None
            logger.info("Circuit breaker manually reset to CLOSED")

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get circuit breaker metrics.

        Returns:
            Dictionary with metrics
        """
        with self._lock:
            return {
                "state": self._state.value,
                "failure_count": self._failure_count,
                "failure_threshold": self.failure_threshold,
                "total_calls": self._metrics.total_calls,
                "success_count": self._metrics.success_count,
                "rejected_count": self._metrics.rejected_count,
                "timeout_seconds": self.timeout,
            }
