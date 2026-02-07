"""Tests for Prometheus metrics collection."""
from typing import Generator

import pytest

from src.metrics.prometheus import MetricsCollector, get_metrics_text, reset_metrics


@pytest.fixture(autouse=True)  # type: ignore[misc]
def reset_prometheus_metrics() -> Generator[None, None, None]:
    """Reset metrics before each test."""
    reset_metrics()
    yield
    reset_metrics()


def test_metrics_collector_singleton() -> None:
    """Test metrics collector is a singleton."""
    collector1 = MetricsCollector.get_instance()
    collector2 = MetricsCollector.get_instance()

    assert collector1 is collector2


def test_token_acquisition_metrics() -> None:
    """Test token acquisition metrics."""
    collector = MetricsCollector.get_instance()

    # Record successful acquisition
    collector.record_token_acquisition(server="test-server", success=True, duration=0.5)

    # Record failed acquisition
    collector.record_token_acquisition(
        server="test-server", success=False, duration=0.3
    )

    metrics_text = get_metrics_text()

    # Check counter metrics
    expected_success = (
        "dicomweb_oauth_token_acquisitions_total{"
        'server="test-server",status="success"} 1.0'
    )
    assert expected_success in metrics_text

    expected_failure = (
        "dicomweb_oauth_token_acquisitions_total{"
        'server="test-server",status="failure"} 1.0'
    )
    assert expected_failure in metrics_text

    # Check histogram metrics (duration)
    assert "dicomweb_oauth_token_acquisition_duration_seconds" in metrics_text


def test_token_cache_metrics() -> None:
    """Test token cache hit/miss metrics."""
    collector = MetricsCollector.get_instance()

    # Record cache hits and misses
    collector.record_cache_hit("test-server")
    collector.record_cache_hit("test-server")
    collector.record_cache_miss("test-server")

    metrics_text = get_metrics_text()

    assert 'dicomweb_oauth_cache_hits_total{server="test-server"} 2.0' in metrics_text
    assert 'dicomweb_oauth_cache_misses_total{server="test-server"} 1.0' in metrics_text


def test_circuit_breaker_metrics() -> None:
    """Test circuit breaker state metrics."""
    collector = MetricsCollector.get_instance()

    # Record circuit breaker state changes
    collector.set_circuit_breaker_state("test-server", "CLOSED")
    collector.record_circuit_breaker_rejection("test-server")

    metrics_text = get_metrics_text()

    assert (
        'dicomweb_oauth_circuit_breaker_state{server="test-server"} 0.0' in metrics_text
    )  # CLOSED=0
    assert (
        'dicomweb_oauth_circuit_breaker_rejections_total{server="test-server"} 1.0'
        in metrics_text
    )


def test_retry_metrics() -> None:
    """Test retry attempt metrics."""
    collector = MetricsCollector.get_instance()

    # Record retry attempts
    collector.record_retry_attempt("test-server", attempt=1, max_attempts=3)
    collector.record_retry_attempt("test-server", attempt=2, max_attempts=3)

    metrics_text = get_metrics_text()

    assert (
        'dicomweb_oauth_retry_attempts_total{server="test-server"} 2.0' in metrics_text
    )


def test_http_request_metrics() -> None:
    """Test HTTP request metrics."""
    collector = MetricsCollector.get_instance()

    # Record HTTP requests
    collector.record_http_request(
        method="POST", endpoint="/token", status_code=200, duration=0.15
    )
    collector.record_http_request(
        method="POST", endpoint="/token", status_code=500, duration=0.05
    )

    metrics_text = get_metrics_text()

    expected_200 = (
        "dicomweb_oauth_http_requests_total{"
        'endpoint="/token",method="POST",status="200"} 1.0'
    )
    assert expected_200 in metrics_text

    expected_500 = (
        "dicomweb_oauth_http_requests_total{"
        'endpoint="/token",method="POST",status="500"} 1.0'
    )
    assert expected_500 in metrics_text

    assert "dicomweb_oauth_http_request_duration_seconds" in metrics_text


def test_error_code_metrics() -> None:
    """Test error code metrics."""
    collector = MetricsCollector.get_instance()

    # Record errors
    collector.record_error(
        "test-server", error_code="TOK-001", category="AUTHENTICATION"
    )
    collector.record_error("test-server", error_code="NET-001", category="NETWORK")

    metrics_text = get_metrics_text()

    expected_auth_error = (
        "dicomweb_oauth_errors_total{"
        'category="AUTHENTICATION",error_code="TOK-001",'
        'server="test-server"} 1.0'
    )
    assert expected_auth_error in metrics_text

    expected_network_error = (
        "dicomweb_oauth_errors_total{"
        'category="NETWORK",error_code="NET-001",'
        'server="test-server"} 1.0'
    )
    assert expected_network_error in metrics_text
