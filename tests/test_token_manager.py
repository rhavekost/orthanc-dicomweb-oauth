import pytest
import responses

from src.token_manager import TokenAcquisitionError, TokenManager


@responses.activate  # type: ignore[misc]
def test_acquire_token_success() -> None:
    """Test successful token acquisition via client credentials flow."""
    responses.add(
        responses.POST,
        "https://login.example.com/oauth2/token",
        json={
            "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
            "token_type": "Bearer",
            "expires_in": 3600,
        },
        status=200,
    )

    config = {
        "TokenEndpoint": "https://login.example.com/oauth2/token",
        "ClientId": "client123",
        "ClientSecret": "secret456",
        "Scope": "https://dicom.example.com/.default",
    }

    manager = TokenManager("test-server", config)
    token = manager.get_token()

    assert token == "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
    assert len(responses.calls) == 1

    # Verify request was formed correctly
    request = responses.calls[0].request
    assert request.headers["Content-Type"] == "application/x-www-form-urlencoded"
    assert "grant_type=client_credentials" in request.body
    assert "client_id=client123" in request.body
    assert "client_secret=secret456" in request.body
    assert "scope=https%3A%2F%2Fdicom.example.com%2F.default" in request.body


@responses.activate  # type: ignore[misc]
def test_token_caching() -> None:
    """Test that valid tokens are cached and reused."""
    responses.add(
        responses.POST,
        "https://login.example.com/oauth2/token",
        json={"access_token": "token123", "token_type": "Bearer", "expires_in": 3600},
        status=200,
    )

    config = {
        "TokenEndpoint": "https://login.example.com/oauth2/token",
        "ClientId": "client123",
        "ClientSecret": "secret456",
        "Scope": "scope",
    }

    manager = TokenManager("test-server", config)

    # First call should acquire token
    token1 = manager.get_token()
    assert token1 == "token123"
    assert len(responses.calls) == 1

    # Second call should use cached token (no new HTTP request)
    token2 = manager.get_token()
    assert token2 == "token123"
    assert len(responses.calls) == 1  # Still only 1 call


@responses.activate  # type: ignore[misc]
def test_token_refresh_before_expiry() -> None:
    """Test that tokens are refreshed before they expire."""
    # First token expires in 10 seconds
    responses.add(
        responses.POST,
        "https://login.example.com/oauth2/token",
        json={"access_token": "token1", "token_type": "Bearer", "expires_in": 10},
        status=200,
    )

    # Second token (after refresh)
    responses.add(
        responses.POST,
        "https://login.example.com/oauth2/token",
        json={"access_token": "token2", "token_type": "Bearer", "expires_in": 3600},
        status=200,
    )

    config = {
        "TokenEndpoint": "https://login.example.com/oauth2/token",
        "ClientId": "client123",
        "ClientSecret": "secret456",
        "Scope": "scope",
        "TokenRefreshBufferSeconds": 300,  # 5 minutes buffer
    }

    manager = TokenManager("test-server", config)

    # First call acquires token (expires in 10 seconds)
    token1 = manager.get_token()
    assert token1 == "token1"
    assert len(responses.calls) == 1

    # Token expires in 10 seconds, but we have 300 second buffer
    # So it should be considered expired and refresh immediately
    token2 = manager.get_token()
    assert token2 == "token2"
    assert len(responses.calls) == 2  # New token acquired


@responses.activate  # type: ignore[misc]
def test_token_acquisition_failure() -> None:
    """Test that token acquisition failures raise TokenAcquisitionError."""
    responses.add(
        responses.POST,
        "https://login.example.com/oauth2/token",
        json={"error": "invalid_client"},
        status=401,
    )

    config = {
        "TokenEndpoint": "https://login.example.com/oauth2/token",
        "ClientId": "invalid_client",
        "ClientSecret": "wrong_secret",
        "Scope": "scope",
    }

    manager = TokenManager("test-server", config)

    with pytest.raises(TokenAcquisitionError, match="Failed to acquire token"):
        manager.get_token()


def test_ssl_verification_enabled_by_default() -> None:
    """Test that SSL verification is enabled by default."""
    config = {
        "TokenEndpoint": "https://login.example.com/oauth2/token",
        "ClientId": "client123",
        "ClientSecret": "secret456",
        "Scope": "scope",
    }

    manager = TokenManager("test-server", config)

    # Verify SSL verification is enabled by default
    assert manager.verify_ssl is True
    assert manager.provider.config.verify_ssl is True


def test_ssl_verification_can_be_disabled_explicitly() -> None:
    """Test that SSL verification can be disabled if explicitly configured."""
    config = {
        "TokenEndpoint": "https://login.example.com/oauth2/token",
        "ClientId": "client123",
        "ClientSecret": "secret456",
        "Scope": "scope",
        "VerifySSL": False,
    }

    manager = TokenManager("test-server", config)

    # Verify SSL verification is disabled when explicitly set to False
    assert manager.verify_ssl is False
    assert manager.provider.config.verify_ssl is False


def test_ssl_verification_with_custom_ca_bundle() -> None:
    """Test that custom CA bundle path can be specified."""
    config = {
        "TokenEndpoint": "https://login.example.com/oauth2/token",
        "ClientId": "client123",
        "ClientSecret": "secret456",
        "Scope": "scope",
        "VerifySSL": "/path/to/ca-bundle.crt",
    }

    manager = TokenManager("test-server", config)

    # Verify custom CA bundle path is set (verify_ssl can be bool or str)
    assert manager.verify_ssl == "/path/to/ca-bundle.crt"
    assert (
        manager.provider.config.verify_ssl  # type: ignore[comparison-overlap]
        == "/path/to/ca-bundle.crt"
    )


def test_token_manager_with_custom_cache() -> None:
    """Test TokenManager can use custom cache backend."""
    from src.cache import MemoryCache

    cache = MemoryCache()

    config = {
        "TokenEndpoint": "https://login.example.com/oauth2/token",
        "ClientId": "client123",
        "ClientSecret": "secret456",
        "Scope": "scope",
    }

    manager = TokenManager("test-server", config, cache=cache)
    assert manager._cache is cache


@responses.activate  # type: ignore[misc]
def test_token_manager_cache_stores_tokens() -> None:
    """Test that acquired tokens are stored in cache backend."""
    from src.cache import MemoryCache

    cache = MemoryCache()

    responses.add(
        responses.POST,
        "https://login.example.com/oauth2/token",
        json={
            "access_token": "cached_token_123",
            "token_type": "Bearer",
            "expires_in": 3600,
        },
        status=200,
    )

    config = {
        "TokenEndpoint": "https://login.example.com/oauth2/token",
        "ClientId": "client123",
        "ClientSecret": "secret456",
        "Scope": "scope",
    }

    manager = TokenManager("test-server", config, cache=cache)
    token = manager.get_token()

    assert token == "cached_token_123"

    # Verify token is in cache backend
    cache_key = "token:test-server"
    assert cache.exists(cache_key) is True

    # Verify cached data structure
    cached_data = cache.get(cache_key)
    assert cached_data is not None
    assert cached_data["access_token"] == "cached_token_123"
    assert "expires_at" in cached_data


@responses.activate  # type: ignore[misc]
def test_token_manager_cache_shares_across_instances() -> None:
    """Test that tokens are shared across multiple TokenManager instances via cache."""
    from src.cache import MemoryCache

    # Shared cache
    shared_cache = MemoryCache()

    responses.add(
        responses.POST,
        "https://login.example.com/oauth2/token",
        json={
            "access_token": "shared_token_456",
            "token_type": "Bearer",
            "expires_in": 3600,
        },
        status=200,
    )

    config = {
        "TokenEndpoint": "https://login.example.com/oauth2/token",
        "ClientId": "client123",
        "ClientSecret": "secret456",
        "Scope": "scope",
    }

    # First instance acquires token
    manager1 = TokenManager("shared-server", config, cache=shared_cache)
    token1 = manager1.get_token()
    assert token1 == "shared_token_456"
    assert len(responses.calls) == 1

    # Second instance should get token from cache (no new HTTP request)
    manager2 = TokenManager("shared-server", config, cache=shared_cache)
    token2 = manager2.get_token()
    assert token2 == "shared_token_456"
    assert len(responses.calls) == 1  # Still only 1 call - cache hit!
