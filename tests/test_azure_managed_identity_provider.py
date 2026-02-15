"""Tests for Azure Managed Identity OAuth provider."""
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
