"""Tests for API versioning."""
import json
from unittest.mock import Mock, patch

from src.dicomweb_oauth_plugin import (
    create_api_response,
    handle_rest_api_servers,
    handle_rest_api_status,
)


def test_api_response_has_version_fields():
    """API responses must include version information."""
    response = create_api_response({"test": "data"})

    assert "plugin_version" in response
    assert "api_version" in response
    assert "timestamp" in response
    assert "data" in response


def test_api_version_format():
    """API version should be Major.Minor format."""
    response = create_api_response({})
    api_version = response["api_version"]

    parts = api_version.split(".")
    assert len(parts) == 2, "API version should be Major.Minor format"
    assert all(part.isdigit() for part in parts), "Version parts must be numeric"


def test_plugin_version_exists():
    """Plugin version must be set."""
    response = create_api_response({})
    assert response["plugin_version"] != ""
    assert isinstance(response["plugin_version"], str)


def test_timestamp_iso8601_format():
    """Timestamp should be ISO 8601 format with UTC timezone."""
    response = create_api_response({})
    timestamp = response["timestamp"]

    assert timestamp.endswith("Z"), "Timestamp must end with Z (UTC)"
    assert "T" in timestamp, "Timestamp must have T separator"


def test_status_endpoint_returns_versioned_response():
    """Status endpoint should return versioned response."""
    output = Mock()

    with patch("src.dicomweb_oauth_plugin.get_plugin_context") as mock_context:
        mock_context.return_value = Mock()
        mock_context.return_value.token_managers = {}
        mock_context.return_value.server_urls = {}

        handle_rest_api_status(output, "/dicomweb-oauth/status")

        call_args = output.AnswerBuffer.call_args
        response_json = call_args[0][0]
        response = json.loads(response_json)

        assert "plugin_version" in response
        assert "api_version" in response


def test_servers_endpoint_returns_versioned_response():
    """Servers endpoint should return versioned response."""
    output = Mock()

    with patch("src.dicomweb_oauth_plugin.get_plugin_context") as mock_context:
        # Mock the context and its methods
        context_mock = Mock()
        mock_token_manager = Mock()
        mock_token_manager.token_endpoint = "https://token.example.com"
        mock_token_manager._cached_token = None

        context_mock.token_managers = {"test": mock_token_manager}
        context_mock.server_urls = {"test": "https://example.com"}
        context_mock.get_server_url.return_value = "https://example.com"

        mock_context.return_value = context_mock

        handle_rest_api_servers(output, "/dicomweb-oauth/servers")

        call_args = output.AnswerBuffer.call_args
        response_json = call_args[0][0]
        response = json.loads(response_json)

        assert "plugin_version" in response
        assert "api_version" in response
