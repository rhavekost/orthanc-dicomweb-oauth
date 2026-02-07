"""Tests for metrics endpoint."""
from unittest.mock import Mock

from src.dicomweb_oauth_plugin import metrics_endpoint
from src.metrics import MetricsCollector, reset_metrics


def test_metrics_endpoint_returns_prometheus_format() -> None:
    """Test metrics endpoint returns Prometheus text format."""
    # Mock output object
    output = Mock()

    # Call metrics endpoint
    metrics_endpoint(output, "/dicomweb-oauth/metrics")

    # Should call AnswerBuffer with metrics text and correct content type
    assert output.AnswerBuffer.called
    call_args = output.AnswerBuffer.call_args

    body = call_args[0][0]
    content_type = call_args[0][1]

    assert content_type == "text/plain; version=0.0.4"
    assert isinstance(body, str)
    assert len(body) > 0


def test_metrics_endpoint_contains_expected_metrics() -> None:
    """Test metrics endpoint contains expected metric names."""
    # Initialize metrics by recording some data
    reset_metrics()
    collector = MetricsCollector.get_instance()
    collector.record_token_acquisition("test-server", success=True, duration=0.1)
    collector.record_cache_hit("test-server")
    collector.set_circuit_breaker_state("test-server", "CLOSED")
    collector.record_error("test-server", "TOK-001", "AUTHENTICATION")

    output = Mock()

    # Call metrics endpoint
    metrics_endpoint(output, "/dicomweb-oauth/metrics")

    # Get the body from the AnswerBuffer call
    body = output.AnswerBuffer.call_args[0][0]

    # Check for expected metric families
    assert "dicomweb_oauth_token_acquisitions_total" in body
    assert "dicomweb_oauth_cache_hits_total" in body
    assert "dicomweb_oauth_circuit_breaker_state" in body
    assert "dicomweb_oauth_errors_total" in body
