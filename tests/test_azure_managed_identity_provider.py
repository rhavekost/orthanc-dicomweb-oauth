"""Tests for Azure Managed Identity OAuth provider."""
from unittest.mock import Mock, patch

import pytest

from src.error_codes import ErrorCode, TokenAcquisitionError
from src.oauth_providers.managed_identity import AzureManagedIdentityProvider


def test_managed_identity_provider_initialization():
    """Test provider initializes with managed identity config."""
    config = {
        "Scope": "https://dicom.healthcareapis.azure.com/.default",
        "VerifySSL": True,
    }

    provider = AzureManagedIdentityProvider(config)

    assert provider.scope == "https://dicom.healthcareapis.azure.com/.default"
    assert provider.verify_ssl is True
    assert provider.provider_name == "azure_managed_identity"


@patch("src.oauth_providers.managed_identity.DefaultAzureCredential")
@patch("src.oauth_providers.managed_identity.time")
def test_acquire_token_success(mock_time, mock_credential_class):
    """Test token acquisition via managed identity."""
    # Setup mock - Azure SDK returns AccessToken with expires_on (timestamp)
    current_time = 1000000
    mock_time.time.return_value = current_time

    mock_credential = Mock()
    mock_token = Mock()
    mock_token.token = "mock_access_token_12345"
    mock_token.expires_on = current_time + 3600  # Expires in 1 hour
    mock_credential.get_token.return_value = mock_token
    mock_credential_class.return_value = mock_credential

    config = {"Scope": "https://dicom.healthcareapis.azure.com/.default"}
    provider = AzureManagedIdentityProvider(config)

    # Act
    token = provider.acquire_token()

    # Assert
    assert token.access_token == "mock_access_token_12345"
    assert token.expires_in == 3600
    assert token.token_type == "Bearer"
    mock_credential.get_token.assert_called_once_with(
        "https://dicom.healthcareapis.azure.com/.default"
    )


@patch("src.oauth_providers.managed_identity.DefaultAzureCredential")
def test_acquire_token_authentication_error(mock_credential_class):
    """Test token acquisition fails with authentication error."""
    from azure.core.exceptions import ClientAuthenticationError

    # Setup mock to raise authentication error
    mock_credential = Mock()
    mock_credential.get_token.side_effect = ClientAuthenticationError(
        "Managed identity not configured"
    )
    mock_credential_class.return_value = mock_credential

    config = {"Scope": "https://dicom.healthcareapis.azure.com/.default"}
    provider = AzureManagedIdentityProvider(config)

    # Act & Assert
    with pytest.raises(TokenAcquisitionError) as exc_info:
        provider.acquire_token()

    assert exc_info.value.error_code == ErrorCode.TOKEN_ACQUISITION_FAILED
    assert "Managed identity authentication failed" in str(exc_info.value)


@patch("src.oauth_providers.managed_identity.DefaultAzureCredential")
def test_acquire_token_empty_token(mock_credential_class):
    """Test token acquisition fails when token is empty."""
    # Setup mock to return None token
    mock_credential = Mock()
    mock_token = Mock()
    mock_token.token = None
    mock_credential.get_token.return_value = mock_token
    mock_credential_class.return_value = mock_credential

    config = {"Scope": "https://dicom.healthcareapis.azure.com/.default"}
    provider = AzureManagedIdentityProvider(config)

    # Act & Assert
    with pytest.raises(TokenAcquisitionError) as exc_info:
        provider.acquire_token()

    assert exc_info.value.error_code == ErrorCode.TOKEN_ACQUISITION_FAILED
    assert "empty token" in str(exc_info.value)


def test_validate_token():
    """Test that managed identity tokens are always considered valid."""
    config = {"Scope": "https://dicom.healthcareapis.azure.com/.default"}
    provider = AzureManagedIdentityProvider(config)

    # Managed identity tokens are pre-validated by Azure
    assert provider.validate_token("any-token") is True
