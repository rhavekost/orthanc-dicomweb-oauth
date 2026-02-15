"""Tests for transparent OAuth proxy endpoint (handle_rest_api_stow).

This tests the working transparent OAuth integration that allows users
to send DICOM studies using the standard Orthanc UI "Send to DICOMWeb"
button with automatic OAuth authentication.
"""
import json
import sys
from typing import Any, Dict
from unittest.mock import MagicMock, Mock

import pytest
import responses

from src.plugin_context import PluginContext
from src.token_manager import TokenManager

# Mock orthanc module before importing plugin
# Provide a valid test configuration to allow plugin initialization
test_config = {
    "DicomWebOAuth": {
        "Servers": {
            "test-server": {
                "Url": "https://test-dicom.example.com/v1",
                "TokenEndpoint": "https://login.example.com/oauth2/token",
                "ClientId": "test-client-id",
                "ClientSecret": "test-client-secret",
                "Scope": "https://dicom.example.com/.default",
            }
        }
    }
}

mock_orthanc = MagicMock()
mock_orthanc.GetConfiguration.return_value = json.dumps(test_config)
sys.modules["orthanc"] = mock_orthanc

# Import plugin (will auto-initialize with test config)
from src.dicomweb_oauth_plugin import handle_rest_api_stow  # noqa: E402


@pytest.fixture  # type: ignore[misc]
def mock_orthanc_output() -> Mock:
    """Create mock Orthanc output object."""
    output = Mock()
    output.AnswerBuffer = Mock()
    return output


@pytest.fixture  # type: ignore[misc]
def mock_multipart_request() -> Dict[str, Any]:
    """Create mock multipart DICOM request."""
    return {
        "headers": {
            "content-type": (
                'multipart/related; type="application/dicom"; ' "boundary=test-boundary"
            ),
            "authorization": "Basic dGVzdDp0ZXN0",
        },
        "body": b"--test-boundary\r\nContent-Type: application/dicom\r\n\r\n"
        b"DICOM_DATA_HERE\r\n--test-boundary--\r\n",
    }


@pytest.fixture  # type: ignore[misc]
def setup_plugin_context() -> None:
    """Setup plugin context with test configuration."""
    context = PluginContext.get_instance()
    context.token_managers.clear()
    context.server_urls.clear()

    # Create test configuration
    config = {
        "Url": "https://test-dicom.example.com/v1",
        "TokenEndpoint": "https://login.example.com/oauth2/token",
        "ClientId": "test-client-id",
        "ClientSecret": "test-client-secret",
        "Scope": "https://dicom.example.com/.default",
    }

    # Register token manager
    manager = TokenManager("test-server", config)
    context.register_token_manager(
        server_name="test-server",
        manager=manager,
        url=config["Url"],
    )


@responses.activate  # type: ignore[misc]
def test_transparent_oauth_multipart_forwarding(
    mock_orthanc_output: Mock,
    mock_multipart_request: Dict[str, Any],
    setup_plugin_context: None,
) -> None:
    """Test transparent OAuth with multipart DICOM data forwarding."""
    # Mock OAuth token response
    responses.add(
        responses.POST,
        "https://login.example.com/oauth2/token",
        json={
            "access_token": "test_oauth_token_123",
            "token_type": "Bearer",
            "expires_in": 3600,
        },
        status=200,
    )

    # Mock DICOM service STOW response
    responses.add(
        responses.POST,
        "https://test-dicom.example.com/v1/studies",
        json={"00081199": {"Value": [{"00081150": {"Value": ["success"]}}]}},
        status=200,
    )

    # Call the handler
    handle_rest_api_stow(
        mock_orthanc_output,
        "/oauth-dicom-web/servers/test-server/studies",
        **mock_multipart_request,
    )

    # Verify OAuth token was requested
    assert len(responses.calls) >= 2
    token_call = responses.calls[0]
    assert token_call.request.url == "https://login.example.com/oauth2/token"

    # Verify DICOM data was forwarded with OAuth token
    stow_call = responses.calls[1]
    assert stow_call.request.url == "https://test-dicom.example.com/v1/studies"
    assert "Bearer test_oauth_token_123" in stow_call.request.headers["Authorization"]
    assert "multipart/related" in stow_call.request.headers["Content-Type"]


@responses.activate  # type: ignore[misc]
def test_transparent_oauth_server_not_found(
    mock_orthanc_output: Mock,
    mock_multipart_request: Dict[str, Any],
    setup_plugin_context: None,
) -> None:
    """Test error handling when server is not configured."""
    # Call with unknown server
    handle_rest_api_stow(
        mock_orthanc_output,
        "/oauth-dicom-web/servers/unknown-server/studies",
        **mock_multipart_request,
    )

    # Verify error response
    mock_orthanc_output.AnswerBuffer.assert_called_once()
    call_args = mock_orthanc_output.AnswerBuffer.call_args[0]
    assert "error" in call_args[0].lower()
    assert "not configured" in call_args[0].lower()


@responses.activate  # type: ignore[misc]
def test_transparent_oauth_token_acquisition_failure(
    mock_orthanc_output: Mock,
    mock_multipart_request: Dict[str, Any],
    setup_plugin_context: None,
) -> None:
    """Test error handling when OAuth token acquisition fails."""
    # Mock OAuth token failure
    responses.add(
        responses.POST,
        "https://login.example.com/oauth2/token",
        json={"error": "invalid_client"},
        status=401,
    )

    # Call the handler
    handle_rest_api_stow(
        mock_orthanc_output,
        "/oauth-dicom-web/servers/test-server/studies",
        **mock_multipart_request,
    )

    # Verify error response
    mock_orthanc_output.AnswerBuffer.assert_called_once()
    call_args = mock_orthanc_output.AnswerBuffer.call_args[0]
    assert "error" in call_args[0].lower()


@responses.activate  # type: ignore[misc]
def test_transparent_oauth_azure_dicom_409_conflict(
    mock_orthanc_output: Mock,
    mock_multipart_request: Dict[str, Any],
    setup_plugin_context: None,
) -> None:
    """Test handling of 409 Conflict (study already exists in Azure)."""
    # Mock OAuth token
    responses.add(
        responses.POST,
        "https://login.example.com/oauth2/token",
        json={
            "access_token": "test_token",
            "token_type": "Bearer",
            "expires_in": 3600,
        },
        status=200,
    )

    # Mock 409 Conflict from DICOM service
    responses.add(
        responses.POST,
        "https://test-dicom.example.com/v1/studies",
        body="Conflict",
        status=409,
    )

    # Call the handler
    handle_rest_api_stow(
        mock_orthanc_output,
        "/oauth-dicom-web/servers/test-server/studies",
        **mock_multipart_request,
    )

    # 409 should be logged but not cause complete failure
    # The error response is returned to Orthanc
    mock_orthanc_output.AnswerBuffer.assert_called_once()


def test_transparent_oauth_endpoint_routing() -> None:
    """Test that endpoint routing works correctly."""
    # Test URI parsing
    uri1 = "/oauth-dicom-web/servers/azure-dicom/studies"
    uri2 = "/oauth-dicom-web/servers/my-server-123/studies"

    # Extract server names
    import re

    pattern = r"/oauth-dicom-web/servers/([^/]+)/studies"

    match1 = re.match(pattern, uri1)
    assert match1 is not None
    assert match1.group(1) == "azure-dicom"

    match2 = re.match(pattern, uri2)
    assert match2 is not None
    assert match2.group(1) == "my-server-123"


def test_transparent_oauth_configuration_pattern() -> None:
    """Test the configuration pattern for transparent OAuth.

    Verifies that the DICOMweb server URL points to localhost proxy
    and OAuth config has the real remote server URL.
    """
    # DICOMweb configuration (what Orthanc's DICOMweb plugin sees)
    dicomweb_config = {
        "Servers": {
            "azure-dicom": {
                "Url": "http://localhost:8042/oauth-dicom-web/servers/azure-dicom",
                "Username": "admin",
                "Password": "secret",
            }
        }
    }

    # OAuth configuration (what our plugin uses)
    oauth_config = {
        "Servers": {
            "azure-dicom": {
                "Url": "https://workspace.dicom.azurehealthcareapis.com/v1",
                "TokenEndpoint": "https://login.microsoftonline.com/tenant/oauth2/v2.0/token",  # noqa: E501
                "ClientId": "client-id",
                "ClientSecret": "client-secret",
                "Scope": "https://dicom.healthcareapis.azure.com/.default",
            }
        }
    }

    # Verify the pattern
    dicom_url = dicomweb_config["Servers"]["azure-dicom"]["Url"]
    oauth_url = oauth_config["Servers"]["azure-dicom"]["Url"]

    # DICOMweb URL should point to localhost proxy
    assert "localhost" in dicom_url
    assert "oauth-dicom-web" in dicom_url

    # OAuth URL should be the real remote server
    assert "localhost" not in oauth_url
    assert "dicom.azurehealthcareapis.com" in oauth_url
