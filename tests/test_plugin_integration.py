from unittest.mock import Mock

import responses

from src.dicomweb_oauth_plugin import initialize_plugin, on_outgoing_http_request


def test_plugin_initialization() -> None:
    """Test that plugin initializes with valid configuration."""
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

    # Should not raise any exception
    initialize_plugin(mock_orthanc)

    # Verify configuration was read
    mock_orthanc.GetConfiguration.assert_called_once()


@responses.activate  # type: ignore[misc]
def test_inject_authorization_header() -> None:
    """Test that Authorization header is injected for configured servers."""
    # Setup mock token response
    responses.add(
        responses.POST,
        "https://login.example.com/oauth2/token",
        json={
            "access_token": "test_token_123",
            "token_type": "Bearer",
            "expires_in": 3600,
        },
        status=200,
    )

    # Initialize plugin
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

    # Make request to configured DICOMweb server
    headers = {"Content-Type": "application/dicom+json"}
    result = on_outgoing_http_request(
        uri="https://dicom.example.com/v2/studies",
        method="GET",
        headers=headers,
        get_params={},
        body=b"",
    )

    # Verify Authorization header was injected
    assert result is not None
    assert "Authorization" in result["headers"]
    assert result["headers"]["Authorization"] == "Bearer test_token_123"


def test_non_oauth_request_passes_through() -> None:
    """Test that requests to non-configured servers pass through unchanged."""
    # Initialize plugin with no matching server
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

    # Make request to different server
    headers = {"Content-Type": "application/dicom+json"}
    result = on_outgoing_http_request(
        uri="https://other-server.com/api/studies",
        method="GET",
        headers=headers,
        get_params={},
        body=b"",
    )

    # Should return None (pass through)
    assert result is None
