"""Tests for token manager resilience features."""
import pytest
from pytest_mock import MockerFixture

from src.oauth_providers.base import OAuthToken, TokenAcquisitionError
from src.resilience.circuit_breaker import CircuitBreakerError, CircuitBreakerState
from src.token_manager import TokenManager


def test_token_manager_circuit_breaker_opens_on_failures(mocker: MockerFixture) -> None:
    """Test circuit breaker opens after threshold failures."""
    config = {
        "TokenEndpoint": "https://test.com/token",
        "ClientId": "test-id",
        "ClientSecret": "test-secret",
        "ResilienceConfig": {
            "CircuitBreakerEnabled": True,
            "CircuitBreakerFailureThreshold": 2,
            "CircuitBreakerTimeout": 1,
        },
    }

    manager = TokenManager("test-server", config)

    # Mock provider to always fail
    mock_provider = mocker.patch.object(manager.provider, "acquire_token")
    mock_provider.side_effect = Exception("Service unavailable")

    # First 2 failures should attempt call
    for _ in range(2):
        with pytest.raises(TokenAcquisitionError):
            manager.get_token()

    # Circuit should now be open
    assert manager._circuit_breaker is not None
    assert manager._circuit_breaker.state == CircuitBreakerState.OPEN

    # Next call should fail fast
    with pytest.raises(CircuitBreakerError):
        manager.get_token()


def test_token_manager_configurable_retry_strategy(mocker: MockerFixture) -> None:
    """Test token manager uses configured retry strategy."""
    config = {
        "TokenEndpoint": "https://test.com/token",
        "ClientId": "test-id",
        "ClientSecret": "test-secret",
        "ResilienceConfig": {
            "RetryMaxAttempts": 3,
            "RetryStrategy": "exponential",
            "RetryInitialDelay": 0.1,
            "RetryMultiplier": 2.0,
        },
    }

    manager = TokenManager("test-server", config)

    call_count = 0

    def failing_then_success() -> OAuthToken:
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise Exception("Not yet")
        return OAuthToken(access_token="token123", expires_in=3600)

    mock_provider = mocker.patch.object(manager.provider, "acquire_token")
    mock_provider.side_effect = failing_then_success

    # Should succeed after retries
    token = manager.get_token()
    assert token == "token123"
    assert call_count == 3


def test_token_manager_circuit_breaker_disabled_by_default(
    mocker: MockerFixture,
) -> None:
    """Test circuit breaker is disabled by default for backward compatibility."""
    config = {
        "TokenEndpoint": "https://test.com/token",
        "ClientId": "test-id",
        "ClientSecret": "test-secret",
    }

    manager = TokenManager("test-server", config)

    # Circuit breaker should be None when disabled
    assert manager._circuit_breaker is None


def test_token_manager_retry_disabled_by_default(mocker: MockerFixture) -> None:
    """Test retry is disabled by default for backward compatibility."""
    config = {
        "TokenEndpoint": "https://test.com/token",
        "ClientId": "test-id",
        "ClientSecret": "test-secret",
    }

    manager = TokenManager("test-server", config)

    # Retry config should be None when disabled
    assert manager._retry_config is None
