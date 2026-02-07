import json
from unittest.mock import Mock

import responses

from src.dicomweb_oauth_plugin import (
    get_plugin_context,
    handle_rest_api_servers,
    handle_rest_api_status,
    handle_rest_api_test_server,
    initialize_plugin,
)


def test_status_endpoint():
    """Test GET /dicomweb-oauth/status returns plugin status."""
    mock_orthanc = Mock()
    mock_orthanc.GetConfiguration.return_value = {
        "DicomWebOAuth": {
            "Servers": {
                "test-server": {
                    "Url": "https://dicom.example.com/v2/",
                    "TokenEndpoint": "https://login.example.com/oauth2/token",
                    "ClientId": "client123",
                    "ClientSecret": "secret456",
                    "Scope": "scope",
                }
            }
        }
    }
    initialize_plugin(mock_orthanc)

    # Call status endpoint
    output = Mock()
    handle_rest_api_status(output, None)

    # Parse response
    response = json.loads(output.AnswerBuffer.call_args[0][0])

    assert response["plugin"] == "DICOMweb OAuth"
    assert response["version"] == "1.0.0"
    assert response["status"] == "active"
    assert response["configured_servers"] == 1


@responses.activate
def test_servers_endpoint():
    """Test GET /dicomweb-oauth/servers returns server details."""
    responses.add(
        responses.POST,
        "https://login.example.com/oauth2/token",
        json={"access_token": "token123", "token_type": "Bearer", "expires_in": 3600},
        status=200,
    )

    mock_orthanc = Mock()
    mock_orthanc.GetConfiguration.return_value = {
        "DicomWebOAuth": {
            "Servers": {
                "test-server": {
                    "Url": "https://dicom.example.com/v2/",
                    "TokenEndpoint": "https://login.example.com/oauth2/token",
                    "ClientId": "client123",
                    "ClientSecret": "secret456",
                    "Scope": "scope",
                }
            }
        }
    }
    initialize_plugin(mock_orthanc)

    # Acquire token first
    context = get_plugin_context()
    context.token_managers["test-server"].get_token()

    # Call servers endpoint
    output = Mock()
    handle_rest_api_servers(output, None)

    # Parse response
    response = json.loads(output.AnswerBuffer.call_args[0][0])

    assert len(response["servers"]) == 1
    assert response["servers"][0]["name"] == "test-server"
    assert response["servers"][0]["url"] == "https://dicom.example.com/v2/"
    assert response["servers"][0]["has_cached_token"] is True
    assert response["servers"][0]["token_valid"] is True


@responses.activate
def test_status_endpoint_no_token_exposure():
    """Test that test server endpoint never exposes token content."""
    responses.add(
        responses.POST,
        "https://login.example.com/oauth2/token",
        json={
            "access_token": "test_token_12345678901234567890",
            "token_type": "Bearer",
            "expires_in": 3600,
        },
        status=200,
    )

    mock_orthanc = Mock()
    mock_orthanc.GetConfiguration.return_value = {
        "DicomWebOAuth": {
            "Servers": {
                "test-server": {
                    "Url": "https://dicom.example.com/v2/",
                    "TokenEndpoint": "https://login.example.com/oauth2/token",
                    "ClientId": "client123",
                    "ClientSecret": "secret456",
                    "Scope": "scope",
                }
            }
        }
    }
    initialize_plugin(mock_orthanc)

    # Call test server endpoint
    output = Mock()
    handle_rest_api_test_server(output, "/dicomweb-oauth/servers/test-server/test")

    # Parse response
    response = json.loads(output.AnswerBuffer.call_args[0][0])

    # Verify no token content is exposed
    assert "token_preview" not in response
    assert "token" not in response
    assert "access_token" not in response
    # Should only have boolean status
    assert "has_token" in response
    assert isinstance(response["has_token"], bool)
