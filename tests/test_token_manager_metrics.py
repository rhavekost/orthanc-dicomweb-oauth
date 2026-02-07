"""Tests for token manager metrics integration."""
from typing import Any, Dict, Generator

import pytest

from src.metrics import get_metrics_text
from src.oauth_providers.base import OAuthToken
from src.token_manager import TokenManager


@pytest.fixture(autouse=True)  # type: ignore[misc]
def reset_metrics() -> Generator[None, None, None]:
    """Reset metrics before each test."""
    from src.metrics.prometheus import reset_metrics

    reset_metrics()
    yield


def test_token_manager_records_cache_hit(mocker: Any) -> None:
    """Test token manager records cache hit metric."""
    config: Dict[str, Any] = {
        "TokenEndpoint": "https://test.com/token",
        "ClientId": "test-id",
        "ClientSecret": "test-secret",
    }

    manager = TokenManager("test-server", config)

    # Prime cache
    mock_provider = mocker.patch.object(manager.provider, "acquire_token")
    mock_provider.return_value = OAuthToken(
        access_token="token123", expires_in=3600, token_type="Bearer"
    )

    manager.get_token()

    # Get from cache
    manager.get_token()

    metrics_text = get_metrics_text()
    assert 'dicomweb_oauth_cache_hits_total{server="test-server"} 1.0' in metrics_text


def test_token_manager_records_cache_miss(mocker: Any) -> None:
    """Test token manager records cache miss metric."""
    config: Dict[str, Any] = {
        "TokenEndpoint": "https://test.com/token",
        "ClientId": "test-id",
        "ClientSecret": "test-secret",
    }

    manager = TokenManager("test-server", config)

    mock_provider = mocker.patch.object(manager.provider, "acquire_token")
    mock_provider.return_value = OAuthToken(
        access_token="token123", expires_in=3600, token_type="Bearer"
    )

    # First call is cache miss
    manager.get_token()

    metrics_text = get_metrics_text()
    assert 'dicomweb_oauth_cache_misses_total{server="test-server"} 1.0' in metrics_text


def test_token_manager_records_acquisition_duration(mocker: Any) -> None:
    """Test token manager records acquisition duration."""
    config: Dict[str, Any] = {
        "TokenEndpoint": "https://test.com/token",
        "ClientId": "test-id",
        "ClientSecret": "test-secret",
    }

    manager = TokenManager("test-server", config)

    mock_provider = mocker.patch.object(manager.provider, "acquire_token")
    mock_provider.return_value = OAuthToken(
        access_token="token123", expires_in=3600, token_type="Bearer"
    )

    manager.get_token()

    metrics_text = get_metrics_text()
    assert "dicomweb_oauth_token_acquisition_duration_seconds" in metrics_text
    assert 'server="test-server"' in metrics_text
