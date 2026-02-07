"""Tests for API rate limiting."""
from src.dicomweb_oauth_plugin import create_flask_app


def test_api_rate_limiting_enabled() -> None:
    """Test that rate limiting is enabled for API endpoints."""
    app = create_flask_app(
        {
            "test-server": {
                "TokenEndpoint": "https://example.com",
                "ClientId": "test",
                "ClientSecret": "secret",
            }
        }
    )

    # Verify rate limiter is attached to app
    assert hasattr(app, "rate_limiter"), "Rate limiter should be attached to app"


def test_test_endpoint_rate_limited() -> None:
    """Test that test endpoint enforces rate limits."""
    config = {
        "test-server": {
            "TokenEndpoint": "https://example.com/token",
            "ClientId": "test",
            "ClientSecret": "secret",
        }
    }

    app = create_flask_app(config, rate_limit_requests=2, rate_limit_window=60)
    client = app.test_client()

    # First 2 requests should succeed (or fail for other reasons, not rate limit)
    client.post("/dicomweb-oauth/servers/test-server/test")
    client.post("/dicomweb-oauth/servers/test-server/test")

    # Third request should be rate limited
    response = client.post("/dicomweb-oauth/servers/test-server/test")
    assert response.status_code == 429, "Should return 429 Too Many Requests"

    # Verify error response
    data = response.get_json()
    assert "error" in data
    assert "rate limit" in data["error"].lower()


def test_status_endpoint_rate_limited() -> None:
    """Test that status endpoint enforces rate limits."""
    config = {
        "test-server": {
            "TokenEndpoint": "https://example.com/token",
            "ClientId": "test",
            "ClientSecret": "secret",
        }
    }

    app = create_flask_app(config, rate_limit_requests=3, rate_limit_window=60)
    client = app.test_client()

    # Use up rate limit
    for _ in range(3):
        client.get("/dicomweb-oauth/status")

    # Next request should be rate limited
    response = client.get("/dicomweb-oauth/status")
    assert response.status_code == 429


def test_different_endpoints_share_rate_limit() -> None:
    """Test that different endpoints share the same rate limit per IP."""
    config = {
        "test-server": {
            "TokenEndpoint": "https://example.com/token",
            "ClientId": "test",
            "ClientSecret": "secret",
        }
    }

    app = create_flask_app(config, rate_limit_requests=2, rate_limit_window=60)
    client = app.test_client()

    # Use limit across different endpoints
    client.get("/dicomweb-oauth/status")
    client.post("/dicomweb-oauth/servers/test-server/test")

    # Third request should be rate limited
    response = client.get("/dicomweb-oauth/status")
    assert response.status_code == 429
