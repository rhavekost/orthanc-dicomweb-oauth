"""Prometheus metrics collection."""
import threading
from typing import Optional, cast

from prometheus_client import (
    REGISTRY,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

# Create separate registry for testing
_custom_registry: Optional[CollectorRegistry] = None


def _get_registry() -> CollectorRegistry:
    """Get the registry (custom for tests, default otherwise)."""
    return _custom_registry if _custom_registry is not None else REGISTRY


class MetricsCollector:
    """
    Singleton metrics collector for Prometheus.

    Collects metrics for token acquisition, caching, circuit breaker, retries, etc.
    """

    _instance: Optional["MetricsCollector"] = None
    _lock: threading.Lock = threading.Lock()

    def __new__(cls) -> "MetricsCollector":
        """Prevent direct instantiation."""
        raise RuntimeError("Use get_instance() instead")

    @classmethod
    def get_instance(cls) -> "MetricsCollector":
        """Get singleton instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    instance = object.__new__(cls)
                    instance._initialize()
                    cls._instance = instance
        return cls._instance

    def _initialize(self) -> None:
        """Initialize metrics."""
        registry = _get_registry()

        # Token acquisition metrics
        self.token_acquisitions = Counter(
            "dicomweb_oauth_token_acquisitions_total",
            "Total token acquisition attempts",
            ["server", "status"],
            registry=registry,
        )

        self.token_acquisition_duration = Histogram(
            "dicomweb_oauth_token_acquisition_duration_seconds",
            "Token acquisition duration",
            ["server"],
            registry=registry,
        )

        # Cache metrics
        self.cache_hits = Counter(
            "dicomweb_oauth_cache_hits_total",
            "Total cache hits",
            ["server"],
            registry=registry,
        )

        self.cache_misses = Counter(
            "dicomweb_oauth_cache_misses_total",
            "Total cache misses",
            ["server"],
            registry=registry,
        )

        # Circuit breaker metrics
        self.circuit_breaker_state = Gauge(
            "dicomweb_oauth_circuit_breaker_state",
            "Circuit breaker state (0=CLOSED, 1=OPEN, 2=HALF_OPEN)",
            ["server"],
            registry=registry,
        )

        self.circuit_breaker_rejections = Counter(
            "dicomweb_oauth_circuit_breaker_rejections_total",
            "Total circuit breaker rejections",
            ["server"],
            registry=registry,
        )

        # Retry metrics
        self.retry_attempts = Counter(
            "dicomweb_oauth_retry_attempts_total",
            "Total retry attempts",
            ["server"],
            registry=registry,
        )

        # HTTP request metrics
        self.http_requests = Counter(
            "dicomweb_oauth_http_requests_total",
            "Total HTTP requests",
            ["method", "endpoint", "status"],
            registry=registry,
        )

        self.http_request_duration = Histogram(
            "dicomweb_oauth_http_request_duration_seconds",
            "HTTP request duration",
            ["method", "endpoint"],
            registry=registry,
        )

        # Error metrics
        self.errors = Counter(
            "dicomweb_oauth_errors_total",
            "Total errors by code and category",
            ["server", "error_code", "category"],
            registry=registry,
        )

    def record_token_acquisition(
        self, server: str, success: bool, duration: float
    ) -> None:
        """Record token acquisition attempt."""
        status = "success" if success else "failure"
        self.token_acquisitions.labels(server=server, status=status).inc()
        self.token_acquisition_duration.labels(server=server).observe(duration)

    def record_cache_hit(self, server: str) -> None:
        """Record cache hit."""
        self.cache_hits.labels(server=server).inc()

    def record_cache_miss(self, server: str) -> None:
        """Record cache miss."""
        self.cache_misses.labels(server=server).inc()

    def set_circuit_breaker_state(self, server: str, state: str) -> None:
        """Set circuit breaker state."""
        state_value = {"CLOSED": 0, "OPEN": 1, "HALF_OPEN": 2}.get(state, 0)
        self.circuit_breaker_state.labels(server=server).set(state_value)

    def record_circuit_breaker_rejection(self, server: str) -> None:
        """Record circuit breaker rejection."""
        self.circuit_breaker_rejections.labels(server=server).inc()

    def record_retry_attempt(
        self, server: str, attempt: int, max_attempts: int
    ) -> None:
        """Record retry attempt."""
        self.retry_attempts.labels(server=server).inc()

    def record_http_request(
        self, method: str, endpoint: str, status_code: int, duration: float
    ) -> None:
        """Record HTTP request."""
        self.http_requests.labels(
            method=method, endpoint=endpoint, status=str(status_code)
        ).inc()
        self.http_request_duration.labels(method=method, endpoint=endpoint).observe(
            duration
        )

    def record_error(self, server: str, error_code: str, category: str) -> None:
        """Record error."""
        self.errors.labels(
            server=server, error_code=error_code, category=category
        ).inc()


def get_metrics_text() -> str:
    """
    Get metrics in Prometheus text format.

    Returns:
        Metrics as text
    """
    return cast(bytes, generate_latest(_get_registry())).decode("utf-8")


def reset_metrics() -> None:
    """Reset metrics (for testing)."""
    global _custom_registry
    _custom_registry = CollectorRegistry()
    MetricsCollector._instance = None
