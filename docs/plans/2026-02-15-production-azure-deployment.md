# Production Azure Deployment Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement production-ready Azure deployment with VNet isolation, private endpoints, and managed identity authentication for Orthanc OAuth proxy.

**Architecture:** Create VNet with service-based subnets (Container Apps, PostgreSQL, Private Endpoints), deploy all backend services with private endpoints, use system-assigned managed identity instead of client credentials, add Python support for managed identity via `azure-identity` library.

**Tech Stack:** Azure Bicep, Python, azure-identity SDK, Azure Container Apps, Private Endpoints, Private DNS Zones

---

## Phase 1: Python Plugin - Managed Identity Support

### Task 1: Add azure-identity dependency

**Files:**
- Modify: `requirements.txt`
- Modify: `Dockerfile` (if needed)

**Step 1: Add azure-identity to requirements**

```bash
echo "azure-identity>=1.15.0" >> requirements.txt
```

**Step 2: Verify dependency format**

Run: `cat requirements.txt | grep azure-identity`
Expected: `azure-identity>=1.15.0`

**Step 3: Commit**

```bash
git add requirements.txt
git commit -m "deps: add azure-identity for managed identity support"
```

---

### Task 2: Create AzureManagedIdentityProvider - Test First

**Files:**
- Create: `tests/test_azure_managed_identity_provider.py`
- Create: `src/oauth_providers/managed_identity.py`

**Step 1: Write failing test for provider initialization**

Create `tests/test_azure_managed_identity_provider.py`:

```python
"""Tests for Azure Managed Identity OAuth provider."""
import os
from unittest.mock import Mock, patch
import pytest
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
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_azure_managed_identity_provider.py::test_managed_identity_provider_initialization -v`
Expected: FAIL with "No module named 'src.oauth_providers.managed_identity'"

**Step 3: Create minimal provider class**

Create `src/oauth_providers/managed_identity.py`:

```python
"""Azure Managed Identity OAuth provider."""
from typing import Any, Dict, Optional

from src.oauth_providers.base import OAuthConfig, OAuthProvider
from src.structured_logger import structured_logger


class AzureManagedIdentityProvider(OAuthProvider):
    """
    Azure Managed Identity OAuth provider.

    Uses DefaultAzureCredential to acquire tokens without client secrets.
    Automatically works in Azure environments with managed identity enabled.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Azure Managed Identity provider.

        Args:
            config: Configuration dictionary with Scope and VerifySSL
        """
        self.scope = config.get("Scope", "https://dicom.healthcareapis.azure.com/.default")
        self.verify_ssl = config.get("VerifySSL", True)
        structured_logger.info("AzureManagedIdentityProvider initialized",
                             scope=self.scope)

    def acquire_token(self) -> Optional[str]:
        """Acquire OAuth token - to be implemented."""
        raise NotImplementedError("acquire_token not yet implemented")

    def validate_token(self, token: str) -> bool:
        """Validate token - managed identity tokens are pre-validated."""
        return True
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_azure_managed_identity_provider.py::test_managed_identity_provider_initialization -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_azure_managed_identity_provider.py src/oauth_providers/managed_identity.py
git commit -m "feat: add AzureManagedIdentityProvider skeleton"
```

---

### Task 3: Implement token acquisition with DefaultAzureCredential

**Files:**
- Modify: `src/oauth_providers/managed_identity.py`
- Modify: `tests/test_azure_managed_identity_provider.py`

**Step 1: Write test for token acquisition**

Add to `tests/test_azure_managed_identity_provider.py`:

```python
@patch('src.oauth_providers.managed_identity.DefaultAzureCredential')
def test_acquire_token_success(mock_credential_class):
    """Test token acquisition via managed identity."""
    # Setup mock
    mock_credential = Mock()
    mock_token = Mock()
    mock_token.token = "mock_access_token_12345"
    mock_credential.get_token.return_value = mock_token
    mock_credential_class.return_value = mock_credential

    config = {
        "Scope": "https://dicom.healthcareapis.azure.com/.default"
    }
    provider = AzureManagedIdentityProvider(config)

    # Act
    token = provider.acquire_token()

    # Assert
    assert token == "mock_access_token_12345"
    mock_credential.get_token.assert_called_once_with(
        "https://dicom.healthcareapis.azure.com/.default"
    )
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_azure_managed_identity_provider.py::test_acquire_token_success -v`
Expected: FAIL with "NotImplementedError: acquire_token not yet implemented"

**Step 3: Implement acquire_token method**

Modify `src/oauth_providers/managed_identity.py`:

```python
"""Azure Managed Identity OAuth provider."""
from typing import Any, Dict, Optional

from azure.identity import DefaultAzureCredential
from azure.core.exceptions import ClientAuthenticationError

from src.oauth_providers.base import OAuthProvider
from src.structured_logger import structured_logger
from src.error_codes import ErrorCode, PluginError


class AzureManagedIdentityProvider(OAuthProvider):
    """
    Azure Managed Identity OAuth provider.

    Uses DefaultAzureCredential to acquire tokens without client secrets.
    Automatically works in Azure environments with managed identity enabled.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Azure Managed Identity provider.

        Args:
            config: Configuration dictionary with Scope and VerifySSL
        """
        self.scope = config.get("Scope", "https://dicom.healthcareapis.azure.com/.default")
        self.verify_ssl = config.get("VerifySSL", True)
        self._credential = None
        structured_logger.info("AzureManagedIdentityProvider initialized",
                             scope=self.scope)

    @property
    def credential(self) -> DefaultAzureCredential:
        """Lazy-load DefaultAzureCredential."""
        if self._credential is None:
            self._credential = DefaultAzureCredential()
        return self._credential

    def acquire_token(self) -> Optional[str]:
        """
        Acquire OAuth token using managed identity.

        Returns:
            Access token string or None if acquisition fails

        Raises:
            PluginError: If token acquisition fails
        """
        try:
            structured_logger.debug("Acquiring token via managed identity",
                                  scope=self.scope)

            token = self.credential.get_token(self.scope)

            if token and token.token:
                structured_logger.info("Token acquired successfully via managed identity")
                return token.token
            else:
                raise PluginError(
                    "Managed identity returned empty token",
                    error_code=ErrorCode.TOKEN_ACQUISITION_FAILED
                )

        except ClientAuthenticationError as e:
            structured_logger.error("Managed identity authentication failed",
                                  error=str(e))
            raise PluginError(
                f"Managed identity authentication failed: {e}",
                error_code=ErrorCode.TOKEN_ACQUISITION_FAILED
            ) from e
        except Exception as e:
            structured_logger.error("Unexpected error acquiring token",
                                  error=str(e))
            raise PluginError(
                f"Token acquisition error: {e}",
                error_code=ErrorCode.TOKEN_ACQUISITION_FAILED
            ) from e

    def validate_token(self, token: str) -> bool:
        """
        Validate token.

        For managed identity tokens, validation is handled by Azure.
        We trust tokens from DefaultAzureCredential.

        Args:
            token: Access token to validate

        Returns:
            Always True for managed identity tokens
        """
        return True
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_azure_managed_identity_provider.py::test_acquire_token_success -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/oauth_providers/managed_identity.py tests/test_azure_managed_identity_provider.py
git commit -m "feat: implement token acquisition via DefaultAzureCredential"
```

---

### Task 4: Add test for token acquisition failure

**Files:**
- Modify: `tests/test_azure_managed_identity_provider.py`

**Step 1: Write test for token acquisition failure**

Add to `tests/test_azure_managed_identity_provider.py`:

```python
from azure.core.exceptions import ClientAuthenticationError
from src.error_codes import PluginError


@patch('src.oauth_providers.managed_identity.DefaultAzureCredential')
def test_acquire_token_authentication_error(mock_credential_class):
    """Test token acquisition handles authentication errors."""
    # Setup mock to raise error
    mock_credential = Mock()
    mock_credential.get_token.side_effect = ClientAuthenticationError("Authentication failed")
    mock_credential_class.return_value = mock_credential

    config = {"Scope": "https://dicom.healthcareapis.azure.com/.default"}
    provider = AzureManagedIdentityProvider(config)

    # Act & Assert
    with pytest.raises(PluginError) as exc_info:
        provider.acquire_token()

    assert "Managed identity authentication failed" in str(exc_info.value)
```

**Step 2: Run test to verify it passes**

Run: `pytest tests/test_azure_managed_identity_provider.py::test_acquire_token_authentication_error -v`
Expected: PASS (code already handles this)

**Step 3: Commit**

```bash
git add tests/test_azure_managed_identity_provider.py
git commit -m "test: add managed identity authentication failure test"
```

---

### Task 5: Update provider factory to support managed identity

**Files:**
- Modify: `src/oauth_providers/factory.py`
- Modify: `tests/test_oauth_providers.py`

**Step 1: Write test for managed identity provider factory**

Add to `tests/test_oauth_providers.py`:

```python
def test_provider_factory_managed_identity():
    """Test factory creates managed identity provider."""
    from src.oauth_providers.factory import create_oauth_provider
    from src.oauth_providers.managed_identity import AzureManagedIdentityProvider

    config = {
        "Type": "AzureManagedIdentity",
        "Scope": "https://dicom.healthcareapis.azure.com/.default"
    }

    provider = create_oauth_provider(config)

    assert isinstance(provider, AzureManagedIdentityProvider)
    assert provider.scope == "https://dicom.healthcareapis.azure.com/.default"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_oauth_providers.py::test_provider_factory_managed_identity -v`
Expected: FAIL (provider type not registered)

**Step 3: Update factory to register managed identity provider**

Modify `src/oauth_providers/factory.py`:

```python
from src.oauth_providers.managed_identity import AzureManagedIdentityProvider

# Add to _PROVIDER_REGISTRY
_PROVIDER_REGISTRY: Dict[str, Type[OAuthProvider]] = {
    "azure": AzureOAuthProvider,
    "generic": GenericOAuth2Provider,
    "aws": AWSCognitoProvider,
    "google": GoogleOAuthProvider,
    "azuremanagedidentity": AzureManagedIdentityProvider,  # Add this
}
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_oauth_providers.py::test_provider_factory_managed_identity -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/oauth_providers/factory.py tests/test_oauth_providers.py
git commit -m "feat: register AzureManagedIdentityProvider in factory"
```

---

### Task 6: Run all tests to ensure no regressions

**Step 1: Run full test suite**

Run: `pytest tests/ -v`
Expected: All tests PASS

**Step 2: Check coverage for managed identity provider**

Run: `pytest tests/test_azure_managed_identity_provider.py --cov=src/oauth_providers/managed_identity --cov-report=term-missing`
Expected: >90% coverage

**Step 3: If coverage is low, add missing tests**

(Skip if coverage is good)

**Step 4: Commit coverage improvements if any**

```bash
git add tests/test_azure_managed_identity_provider.py
git commit -m "test: improve managed identity provider coverage"
```

---

## Phase 2: Bicep Infrastructure - Network Foundation

### Task 7: Create network module with VNet and subnets

**Files:**
- Create: `examples/azure/production/modules/network.bicep`

**Step 1: Create network module**

Create `examples/azure/production/modules/network.bicep`:

```bicep
// ========================================
// Network Infrastructure Module
// ========================================
// Creates VNet with service-based subnets for production deployment

@description('The name of the virtual network')
param vnetName string

@description('The location for the network resources')
param location string

@description('VNet address prefix')
param vnetAddressPrefix string = '10.0.0.0/16'

@description('Container Apps subnet address prefix')
param containerAppsSubnetPrefix string = '10.0.0.0/23'

@description('PostgreSQL subnet address prefix')
param postgresSubnetPrefix string = '10.0.2.0/24'

@description('Private endpoints subnet address prefix')
param privateEndpointsSubnetPrefix string = '10.0.3.0/24'

@description('Resource tags')
param tags object = {}

// ========================================
// Virtual Network
// ========================================

resource vnet 'Microsoft.Network/virtualNetworks@2023-05-01' = {
  name: vnetName
  location: location
  tags: tags
  properties: {
    addressSpace: {
      addressPrefixes: [
        vnetAddressPrefix
      ]
    }
    subnets: [
      {
        name: 'snet-container-apps'
        properties: {
          addressPrefix: containerAppsSubnetPrefix
          serviceEndpoints: []
          delegations: []
        }
      }
      {
        name: 'snet-postgres'
        properties: {
          addressPrefix: postgresSubnetPrefix
          serviceEndpoints: []
          delegations: [
            {
              name: 'Microsoft.DBforPostgreSQL.flexibleServers'
              properties: {
                serviceName: 'Microsoft.DBforPostgreSQL/flexibleServers'
              }
            }
          ]
        }
      }
      {
        name: 'snet-private-endpoints'
        properties: {
          addressPrefix: privateEndpointsSubnetPrefix
          serviceEndpoints: []
          delegations: []
          privateEndpointNetworkPolicies: 'Disabled'
        }
      }
    ]
  }
}

// ========================================
// Outputs
// ========================================

output vnetId string = vnet.id
output vnetName string = vnet.name
output containerAppsSubnetId string = vnet.properties.subnets[0].id
output postgresSubnetId string = vnet.properties.subnets[1].id
output privateEndpointsSubnetId string = vnet.properties.subnets[2].id
```

**Step 2: Verify Bicep syntax**

Run: `az bicep build --file examples/azure/production/modules/network.bicep`
Expected: No errors, creates network.json

**Step 3: Commit**

```bash
git add examples/azure/production/modules/network.bicep
git commit -m "feat: add network module with VNet and subnets"
```

---

### Task 8: Create Private DNS zones module

**Files:**
- Create: `examples/azure/production/modules/private-dns.bicep`

**Step 1: Create private DNS module**

Create `examples/azure/production/modules/private-dns.bicep`:

```bicep
// ========================================
// Private DNS Zones Module
// ========================================
// Creates and links Private DNS zones to VNet

@description('The location for the resources')
param location string

@description('The ID of the VNet to link DNS zones to')
param vnetId string

@description('Resource tags')
param tags object = {}

// ========================================
// Private DNS Zones
// ========================================

resource postgresDnsZone 'Microsoft.Network/privateDnsZones@2020-06-01' = {
  name: 'privatelink.postgres.database.azure.com'
  location: 'global'
  tags: tags
}

resource blobDnsZone 'Microsoft.Network/privateDnsZones@2020-06-01' = {
  name: 'privatelink.blob.core.windows.net'
  location: 'global'
  tags: tags
}

resource acrDnsZone 'Microsoft.Network/privateDnsZones@2020-06-01' = {
  name: 'privatelink.azurecr.io'
  location: 'global'
  tags: tags
}

// ========================================
// VNet Links
// ========================================

resource postgresVnetLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2020-06-01' = {
  parent: postgresDnsZone
  name: 'postgres-vnet-link'
  location: 'global'
  tags: tags
  properties: {
    registrationEnabled: false
    virtualNetwork: {
      id: vnetId
    }
  }
}

resource blobVnetLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2020-06-01' = {
  parent: blobDnsZone
  name: 'blob-vnet-link'
  location: 'global'
  tags: tags
  properties: {
    registrationEnabled: false
    virtualNetwork: {
      id: vnetId
    }
  }
}

resource acrVnetLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2020-06-01' = {
  parent: acrDnsZone
  name: 'acr-vnet-link'
  location: 'global'
  tags: tags
  properties: {
    registrationEnabled: false
    virtualNetwork: {
      id: vnetId
    }
  }
}

// ========================================
// Outputs
// ========================================

output postgresDnsZoneId string = postgresDnsZone.id
output blobDnsZoneId string = blobDnsZone.id
output acrDnsZoneId string = acrDnsZone.id
```

**Step 2: Verify Bicep syntax**

Run: `az bicep build --file examples/azure/production/modules/private-dns.bicep`
Expected: No errors

**Step 3: Commit**

```bash
git add examples/azure/production/modules/private-dns.bicep
git commit -m "feat: add Private DNS zones module"
```

---

### Task 9: Create reusable private endpoint module

**Files:**
- Create: `examples/azure/production/modules/private-endpoint.bicep`

**Step 1: Create private endpoint module**

Create `examples/azure/production/modules/private-endpoint.bicep`:

```bicep
// ========================================
// Private Endpoint Module (Reusable)
// ========================================
// Creates a private endpoint for any Azure service

@description('The name of the private endpoint')
param privateEndpointName string

@description('The location for the private endpoint')
param location string

@description('The ID of the subnet for the private endpoint')
param subnetId string

@description('The ID of the resource to create private endpoint for')
param privateLinkServiceId string

@description('The group IDs for the private endpoint (e.g., blob, registry)')
param groupIds array

@description('The ID of the Private DNS zone for automatic registration')
param privateDnsZoneId string

@description('Resource tags')
param tags object = {}

// ========================================
// Private Endpoint
// ========================================

resource privateEndpoint 'Microsoft.Network/privateEndpoints@2023-05-01' = {
  name: privateEndpointName
  location: location
  tags: tags
  properties: {
    subnet: {
      id: subnetId
    }
    privateLinkServiceConnections: [
      {
        name: privateEndpointName
        properties: {
          privateLinkServiceId: privateLinkServiceId
          groupIds: groupIds
        }
      }
    ]
  }
}

// ========================================
// Private DNS Zone Group
// ========================================

resource privateDnsZoneGroup 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2023-05-01' = {
  parent: privateEndpoint
  name: 'default'
  properties: {
    privateDnsZoneConfigs: [
      {
        name: 'config1'
        properties: {
          privateDnsZoneId: privateDnsZoneId
        }
      }
    ]
  }
}

// ========================================
// Outputs
// ========================================

output privateEndpointId string = privateEndpoint.id
output privateEndpointName string = privateEndpoint.name
```

**Step 2: Verify Bicep syntax**

Run: `az bicep build --file examples/azure/production/modules/private-endpoint.bicep`
Expected: No errors

**Step 3: Commit**

```bash
git add examples/azure/production/modules/private-endpoint.bicep
git commit -m "feat: add reusable private endpoint module"
```

---

## Phase 3: Bicep Infrastructure - Storage and Registry with Private Endpoints

### Task 10: Update Storage module to support private endpoint

**Files:**
- Create: `examples/azure/production/modules/storage.bicep`

**Step 1: Create storage module with private endpoint support**

Create `examples/azure/production/modules/storage.bicep`:

```bicep
// ========================================
// Storage Account Module with Private Endpoint
// ========================================

@description('The name of the storage account')
param storageAccountName string

@description('The location for the storage account')
param location string

@description('The ID of the subnet for private endpoint')
param privateEndpointSubnetId string

@description('The ID of the blob Private DNS zone')
param blobPrivateDnsZoneId string

@description('Disable public network access')
param publicNetworkAccess string = 'Disabled'

@description('Resource tags')
param tags object = {}

// ========================================
// Storage Account
// ========================================

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: storageAccountName
  location: location
  tags: tags
  kind: 'StorageV2'
  sku: {
    name: 'Standard_LRS'
  }
  properties: {
    accessTier: 'Hot'
    allowBlobPublicAccess: false
    publicNetworkAccess: publicNetworkAccess
    networkAcls: {
      defaultAction: 'Deny'
      bypass: 'None'
    }
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
  }
}

// ========================================
// Blob Service
// ========================================

resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' = {
  parent: storageAccount
  name: 'default'
  properties: {
    deleteRetentionPolicy: {
      enabled: true
      days: 7
    }
  }
}

// ========================================
// Orthanc Container
// ========================================

resource orthancContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = {
  parent: blobService
  name: 'orthanc'
  properties: {
    publicAccess: 'None'
  }
}

// ========================================
// Private Endpoint
// ========================================

module blobPrivateEndpoint '../private-endpoint.bicep' = {
  name: '${storageAccountName}-blob-pe'
  params: {
    privateEndpointName: '${storageAccountName}-blob-pe'
    location: location
    subnetId: privateEndpointSubnetId
    privateLinkServiceId: storageAccount.id
    groupIds: ['blob']
    privateDnsZoneId: blobPrivateDnsZoneId
    tags: tags
  }
}

// ========================================
// Outputs
// ========================================

output storageAccountId string = storageAccount.id
output storageAccountName string = storageAccount.name
output blobEndpoint string = storageAccount.properties.primaryEndpoints.blob
output containerName string = orthancContainer.name
```

**Step 2: Verify Bicep syntax**

Run: `az bicep build --file examples/azure/production/modules/storage.bicep`
Expected: No errors

**Step 3: Commit**

```bash
git add examples/azure/production/modules/storage.bicep
git commit -m "feat: add storage module with private endpoint"
```

---

### Task 11: Update Container Registry module with private endpoint

**Files:**
- Create: `examples/azure/production/modules/container-registry.bicep` (production version)

**Step 1: Create ACR module with private endpoint**

Create `examples/azure/production/modules/container-registry.bicep`:

```bicep
// ========================================
// Container Registry Module with Private Endpoint
// ========================================

@description('The name of the container registry')
param registryName string

@description('The location for the registry')
param location string

@description('The ID of the subnet for private endpoint')
param privateEndpointSubnetId string

@description('The ID of the ACR Private DNS zone')
param acrPrivateDnsZoneId string

@description('The SKU for the registry')
param sku string = 'Basic'

@description('Disable admin user')
param adminUserEnabled bool = false

@description('Disable public network access')
param publicNetworkAccess string = 'Disabled'

@description('Resource tags')
param tags object = {}

// ========================================
// Container Registry
// ========================================

resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: registryName
  location: location
  tags: tags
  sku: {
    name: sku
  }
  properties: {
    adminUserEnabled: adminUserEnabled
    publicNetworkAccess: publicNetworkAccess
    networkRuleBypassOptions: 'AzureServices'
    zoneRedundancy: 'Disabled'
  }
}

// ========================================
// Private Endpoint
// ========================================

module acrPrivateEndpoint '../private-endpoint.bicep' = {
  name: '${registryName}-pe'
  params: {
    privateEndpointName: '${registryName}-pe'
    location: location
    subnetId: privateEndpointSubnetId
    privateLinkServiceId: containerRegistry.id
    groupIds: ['registry']
    privateDnsZoneId: acrPrivateDnsZoneId
    tags: tags
  }
}

// ========================================
// Outputs
// ========================================

output registryId string = containerRegistry.id
output registryName string = containerRegistry.name
output loginServer string = containerRegistry.properties.loginServer
```

**Step 2: Verify Bicep syntax**

Run: `az bicep build --file examples/azure/production/modules/container-registry.bicep`
Expected: No errors

**Step 3: Commit**

```bash
git add examples/azure/production/modules/container-registry.bicep
git commit -m "feat: add ACR module with private endpoint"
```

---

## Phase 4: Bicep Infrastructure - Container App with Managed Identity

### Task 12: Create Container App module with managed identity and VNet integration

**Files:**
- Create: `examples/azure/production/modules/container-app.bicep`

**Step 1: Create Container App module**

Create `examples/azure/production/modules/container-app.bicep`:

```bicep
// ========================================
// Container App Module with Managed Identity and VNet Integration
// ========================================

@description('The name of the Container App')
param containerAppName string

@description('The name of the Container Apps Environment')
param environmentName string

@description('The location for the Container App')
param location string

@description('The container image to deploy')
param containerImage string

@description('The ID of the Container Apps subnet')
param containerAppsSubnetId string

@description('Orthanc admin username')
param orthancUsername string

@description('Orthanc admin password')
@secure()
param orthancPassword string

@description('PostgreSQL connection string')
@secure()
param postgresConnectionString string

@description('Storage account name')
param storageAccountName string

@description('Storage container name')
param storageContainerName string

@description('DICOM service URL')
param dicomServiceUrl string

@description('Resource tags')
param tags object = {}

// ========================================
// Container Apps Environment
// ========================================

resource environment 'Microsoft.App/managedEnvironments@2023-05-01' = {
  name: environmentName
  location: location
  tags: tags
  properties: {
    vnetConfiguration: {
      infrastructureSubnetId: containerAppsSubnetId
      internal: false  // External ingress
    }
    zoneRedundant: false
  }
}

// ========================================
// Container App
// ========================================

resource containerApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: containerAppName
  location: location
  tags: tags
  identity: {
    type: 'SystemAssigned'  // Enable system-assigned managed identity
  }
  properties: {
    environmentId: environment.id
    configuration: {
      ingress: {
        external: true
        targetPort: 8042
        transport: 'http'
        allowInsecure: false
      }
      secrets: [
        {
          name: 'orthanc-password'
          value: orthancPassword
        }
        {
          name: 'postgres-connection-string'
          value: postgresConnectionString
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'orthanc-oauth'
          image: containerImage
          resources: {
            cpu: json('1.0')
            memory: '2Gi'
          }
          env: [
            {
              name: 'ORTHANC_USERNAME'
              value: orthancUsername
            }
            {
              name: 'ORTHANC_PASSWORD'
              secretRef: 'orthanc-password'
            }
            {
              name: 'POSTGRES_CONNECTION_STRING'
              secretRef: 'postgres-connection-string'
            }
            {
              name: 'AZURE_STORAGE_ACCOUNT'
              value: storageAccountName
            }
            {
              name: 'AZURE_STORAGE_CONTAINER'
              value: storageContainerName
            }
            {
              name: 'DICOM_SERVICE_URL'
              value: dicomServiceUrl
            }
            {
              name: 'USE_MANAGED_IDENTITY'
              value: 'true'
            }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 3
      }
    }
  }
}

// ========================================
// Outputs
// ========================================

output containerAppId string = containerApp.id
output containerAppName string = containerApp.name
output containerAppUrl string = containerApp.properties.configuration.ingress.fqdn
output containerAppPrincipalId string = containerApp.identity.principalId
output environmentId string = environment.id
```

**Step 2: Verify Bicep syntax**

Run: `az bicep build --file examples/azure/production/modules/container-app.bicep`
Expected: No errors

**Step 3: Commit**

```bash
git add examples/azure/production/modules/container-app.bicep
git commit -m "feat: add Container App module with managed identity"
```

---

### Task 13: Create RBAC assignments module

**Files:**
- Create: `examples/azure/production/modules/rbac-assignments.bicep`

**Step 1: Create RBAC module**

Create `examples/azure/production/modules/rbac-assignments.bicep`:

```bicep
// ========================================
// RBAC Assignments Module
// ========================================
// Assigns roles to Container App managed identity

@description('The principal ID of the Container App managed identity')
param containerAppPrincipalId string

@description('The ID of the DICOM service')
param dicomServiceId string

@description('The ID of the storage account')
param storageAccountId string

@description('The ID of the container registry')
param containerRegistryId string

// ========================================
// Built-in Role IDs
// ========================================

var dicomDataOwnerRoleId = '58a3b984-7adf-4c20-983a-32417c86fbc8'
var storageBlobDataContributorRoleId = 'ba92f5b4-2d11-453d-a403-e96b0029c9fe'
var acrPullRoleId = '7f951dda-4ed3-4680-a7ca-43fe172d538d'

// ========================================
// DICOM Data Owner Assignment
// ========================================

resource dicomRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: resourceId('Microsoft.HealthcareApis/workspaces/dicomservices', split(dicomServiceId, '/')[8], split(dicomServiceId, '/')[10])
  name: guid(dicomServiceId, containerAppPrincipalId, dicomDataOwnerRoleId)
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', dicomDataOwnerRoleId)
    principalId: containerAppPrincipalId
    principalType: 'ServicePrincipal'
  }
}

// ========================================
// Storage Blob Data Contributor Assignment
// ========================================

resource storageRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: resourceId('Microsoft.Storage/storageAccounts', split(storageAccountId, '/')[8])
  name: guid(storageAccountId, containerAppPrincipalId, storageBlobDataContributorRoleId)
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', storageBlobDataContributorRoleId)
    principalId: containerAppPrincipalId
    principalType: 'ServicePrincipal'
  }
}

// ========================================
// ACR Pull Assignment
// ========================================

resource acrRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: resourceId('Microsoft.ContainerRegistry/registries', split(containerRegistryId, '/')[8])
  name: guid(containerRegistryId, containerAppPrincipalId, acrPullRoleId)
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', acrPullRoleId)
    principalId: containerAppPrincipalId
    principalType: 'ServicePrincipal'
  }
}

// ========================================
// Outputs
// ========================================

output dicomRoleAssignmentId string = dicomRoleAssignment.id
output storageRoleAssignmentId string = storageRoleAssignment.id
output acrRoleAssignmentId string = acrRoleAssignment.id
```

**Step 2: Verify Bicep syntax**

Run: `az bicep build --file examples/azure/production/modules/rbac-assignments.bicep`
Expected: No errors

**Step 3: Commit**

```bash
git add examples/azure/production/modules/rbac-assignments.bicep
git commit -m "feat: add RBAC assignments module"
```

---

## Phase 5: Main Orchestration and Deployment Script

### Task 14: Create main.bicep orchestration

**Files:**
- Create: `examples/azure/production/main.bicep`

**Step 1: Create main.bicep (first half - network and data services)**

Create `examples/azure/production/main.bicep`:

```bicep
targetScope = 'subscription'

// ========================================
// Parameters
// ========================================

@description('The name of the environment')
param environmentName string

@description('The Azure region')
param location string

@description('The name of the resource group')
param resourceGroupName string

@description('Orthanc admin username')
param orthancUsername string

@description('Orthanc admin password')
@secure()
param orthancPassword string

@description('PostgreSQL admin username')
param postgresAdminUsername string

@description('PostgreSQL admin password')
@secure()
param postgresAdminPassword string

@description('VNet address prefix')
param vnetAddressPrefix string = '10.0.0.0/16'

@description('Resource tags')
param tags object = {}

// ========================================
// Variables
// ========================================

var resourcePrefix = 'orthanc-${environmentName}'
var vnetName = '${resourcePrefix}-vnet'
var storageAccountName = toLower(take(replace('${resourcePrefix}sa${uniqueString(subscription().subscriptionId, resourceGroupName)}', '-', ''), 24))
var containerRegistryName = toLower(take(replace('${resourcePrefix}acr${uniqueString(subscription().subscriptionId, resourceGroupName)}', '-', ''), 50))
var postgresServerName = '${resourcePrefix}-db-${uniqueString(subscription().subscriptionId, resourceGroupName)}'
var healthcareWorkspaceName = toLower('orthws${uniqueString(subscription().subscriptionId, resourceGroupName)}')
var dicomServiceName = '${resourcePrefix}-dicom'
var containerAppName = '${resourcePrefix}-app'
var environmentNameContainerApps = '${resourcePrefix}-cae'

// ========================================
// Resource Group
// ========================================

resource rg 'Microsoft.Resources/resourceGroups@2024-03-01' = {
  name: resourceGroupName
  location: location
  tags: tags
}

// ========================================
// Network Infrastructure
// ========================================

module network './modules/network.bicep' = {
  scope: rg
  name: 'networkDeployment'
  params: {
    vnetName: vnetName
    location: location
    vnetAddressPrefix: vnetAddressPrefix
    tags: tags
  }
}

module privateDns './modules/private-dns.bicep' = {
  scope: rg
  name: 'privateDnsDeployment'
  params: {
    location: location
    vnetId: network.outputs.vnetId
    tags: tags
  }
}

// ========================================
// Storage Account with Private Endpoint
// ========================================

module storage './modules/storage.bicep' = {
  scope: rg
  name: 'storageDeployment'
  params: {
    storageAccountName: storageAccountName
    location: location
    privateEndpointSubnetId: network.outputs.privateEndpointsSubnetId
    blobPrivateDnsZoneId: privateDns.outputs.blobDnsZoneId
    tags: tags
  }
  dependsOn: [
    privateDns
  ]
}

// ========================================
// Container Registry with Private Endpoint
// ========================================

module containerRegistry './modules/container-registry.bicep' = {
  scope: rg
  name: 'containerRegistryDeployment'
  params: {
    registryName: containerRegistryName
    location: location
    privateEndpointSubnetId: network.outputs.privateEndpointsSubnetId
    acrPrivateDnsZoneId: privateDns.outputs.acrDnsZoneId
    sku: 'Basic'
    tags: tags
  }
  dependsOn: [
    privateDns
  ]
}

// Outputs to be continued in next step...
```

**Step 2: Continue main.bicep (second half - PostgreSQL, DICOM, Container App)**

Continue in `examples/azure/production/main.bicep`:

```bicep
// ========================================
// PostgreSQL Flexible Server with VNet Integration
// ========================================

module postgres 'br/public:avm/res/db-for-postgre-sql/flexible-server:0.8.0' = {
  scope: rg
  name: 'postgresDeployment'
  params: {
    name: postgresServerName
    location: location
    tags: tags
    skuName: 'Standard_B2s'
    tier: 'Burstable'
    storageSizeGB: 32
    version: '15'
    administratorLogin: postgresAdminUsername
    administratorLoginPassword: postgresAdminPassword
    highAvailability: 'Disabled'
    databases: [
      {
        name: 'orthanc'
      }
    ]
    delegatedSubnetResourceId: network.outputs.postgresSubnetId
    privateDnsZoneArmResourceId: privateDns.outputs.postgresDnsZoneId
  }
  dependsOn: [
    network
    privateDns
  ]
}

module postgresConfig '../../quickstart/modules/postgres-config.bicep' = {
  scope: rg
  name: 'postgresConfigDeployment'
  params: {
    postgresServerName: postgresServerName
  }
  dependsOn: [
    postgres
  ]
}

// ========================================
// Healthcare Workspace and DICOM Service
// ========================================

module healthcareWorkspace '../../quickstart/modules/healthcare-workspace.bicep' = {
  scope: rg
  name: 'healthcareWorkspaceDeployment'
  params: {
    workspaceName: healthcareWorkspaceName
    dicomServiceName: dicomServiceName
    location: location
    tags: tags
  }
}

// ========================================
// Container App with Managed Identity
// ========================================

var containerImage = '${containerRegistryName}.azurecr.io/orthanc-oauth:latest'
var postgresConnectionString = 'host=${postgresServerName}.postgres.database.azure.com port=5432 dbname=orthanc user=${postgresAdminUsername} password=${postgresAdminPassword} sslmode=require'

module containerApp './modules/container-app.bicep' = {
  scope: rg
  name: 'containerAppDeployment'
  params: {
    containerAppName: containerAppName
    environmentName: environmentNameContainerApps
    location: location
    containerImage: containerImage
    containerAppsSubnetId: network.outputs.containerAppsSubnetId
    orthancUsername: orthancUsername
    orthancPassword: orthancPassword
    postgresConnectionString: postgresConnectionString
    storageAccountName: storageAccountName
    storageContainerName: storage.outputs.containerName
    dicomServiceUrl: healthcareWorkspace.outputs.dicomServiceUrl
    tags: tags
  }
  dependsOn: [
    network
    storage
    postgres
    healthcareWorkspace
  ]
}

// ========================================
// RBAC Assignments
// ========================================

module rbacAssignments './modules/rbac-assignments.bicep' = {
  scope: rg
  name: 'rbacAssignmentsDeployment'
  params: {
    containerAppPrincipalId: containerApp.outputs.containerAppPrincipalId
    dicomServiceId: healthcareWorkspace.outputs.dicomServiceId
    storageAccountId: storage.outputs.storageAccountId
    containerRegistryId: containerRegistry.outputs.registryId
  }
  dependsOn: [
    containerApp
  ]
}

// ========================================
// Outputs
// ========================================

output resourceGroupName string = rg.name
output containerAppUrl string = containerApp.outputs.containerAppUrl
output containerRegistryName string = containerRegistry.outputs.registryName
output containerRegistryLoginServer string = containerRegistry.outputs.loginServer
output dicomServiceUrl string = healthcareWorkspace.outputs.dicomServiceUrl
output postgresServerFqdn string = '${postgresServerName}.postgres.database.azure.com'
output storageAccountName string = storage.outputs.storageAccountName
output vnetId string = network.outputs.vnetId
```

**Step 3: Verify Bicep syntax**

Run: `az bicep build --file examples/azure/production/main.bicep`
Expected: No errors

**Step 4: Commit**

```bash
git add examples/azure/production/main.bicep
git commit -m "feat: add main orchestration Bicep template"
```

---

### Task 15: Create deployment script

**Files:**
- Create: `examples/azure/production/deploy.sh`

**Step 1: Create deploy.sh script**

Create `examples/azure/production/deploy.sh`:

```bash
#!/bin/bash
set -e

# ========================================
# Orthanc OAuth Production Deployment
# ========================================

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../../.." && pwd )"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "============================================================================"
echo "Orthanc OAuth Production Deployment"
echo "Production-ready with VNet isolation and private endpoints"
echo "============================================================================"
echo ""

# ========================================
# Phase 1: Configuration
# ========================================

ENV_NAME="${ENV_NAME:-production}"
LOCATION="${LOCATION:-westus2}"
RG_NAME="rg-orthanc-${ENV_NAME}"

echo -e "${BLUE}→ Phase 1/5: Configuration${NC}"
echo "  Environment: $ENV_NAME"
echo "  Location: $LOCATION"
echo "  Resource Group: $RG_NAME"
echo ""

# Generate passwords
ORTHANC_PASSWORD=$(openssl rand -base64 32)
POSTGRES_PASSWORD=$(openssl rand -base64 32)

# ========================================
# Phase 2: Deploy Network Infrastructure
# ========================================

echo -e "${BLUE}→ Phase 2/5: Deploying network infrastructure${NC}"
echo "  This creates VNet, subnets, and Private DNS zones"
echo ""

DEPLOYMENT_NAME="orthanc-prod-network-$(date +%Y%m%d-%H%M%S)"

az deployment sub create \
  --name "$DEPLOYMENT_NAME" \
  --location "$LOCATION" \
  --template-file "$SCRIPT_DIR/main.bicep" \
  --parameters \
    environmentName="$ENV_NAME" \
    location="$LOCATION" \
    resourceGroupName="$RG_NAME" \
    orthancUsername="admin" \
    orthancPassword="$ORTHANC_PASSWORD" \
    postgresAdminUsername="orthanc_admin" \
    postgresAdminPassword="$POSTGRES_PASSWORD" \
  --query properties.outputs \
  -o json > "$SCRIPT_DIR/deployment-output.json"

if [ $? -ne 0 ]; then
  echo -e "${YELLOW}✗ Infrastructure deployment failed${NC}"
  exit 1
fi

echo -e "${GREEN}✓ Infrastructure deployed${NC}"
echo ""

# ========================================
# Phase 3: Extract Deployment Details
# ========================================

echo -e "${BLUE}→ Phase 3/5: Extracting deployment details${NC}"

ACR_NAME=$(jq -r '.containerRegistryName.value' "$SCRIPT_DIR/deployment-output.json")
ACR_LOGIN_SERVER=$(jq -r '.containerRegistryLoginServer.value' "$SCRIPT_DIR/deployment-output.json")
CONTAINER_APP_URL=$(jq -r '.containerAppUrl.value' "$SCRIPT_DIR/deployment-output.json")

echo "  Container Registry: $ACR_NAME"
echo "  Container App URL: $CONTAINER_APP_URL"
echo ""

# ========================================
# Phase 4: Build and Push Docker Image
# ========================================

echo -e "${BLUE}→ Phase 4/5: Building and pushing Docker image${NC}"
echo "  CRITICAL: Building for linux/amd64 platform"
echo ""

# Login to ACR using managed identity from local machine
az acr login --name "$ACR_NAME"

# Build and push image
cd "$PROJECT_ROOT"
docker buildx build \
  --platform linux/amd64 \
  -t "${ACR_LOGIN_SERVER}/orthanc-oauth:latest" \
  -f examples/azure/quickstart/Dockerfile \
  --push \
  .

echo -e "${GREEN}✓ Docker image built and pushed${NC}"
echo ""

# ========================================
# Phase 5: Restart Container App
# ========================================

echo -e "${BLUE}→ Phase 5/5: Restarting Container App${NC}"

CONTAINER_APP_NAME=$(az containerapp list -g "$RG_NAME" --query "[0].name" -o tsv)
az containerapp revision restart \
  --name "$CONTAINER_APP_NAME" \
  --resource-group "$RG_NAME" \
  --revision latest

echo -e "${GREEN}✓ Container App restarted${NC}"
echo ""

# ========================================
# Deployment Complete
# ========================================

echo "============================================================================"
echo -e "${GREEN}Production Deployment Complete!${NC}"
echo "============================================================================"
echo ""
echo "Access Information:"
echo "  Orthanc URL: https://${CONTAINER_APP_URL}"
echo "  Username: admin"
echo "  Password: ${ORTHANC_PASSWORD}"
echo ""
echo "Credentials saved to: $SCRIPT_DIR/deployment-output.json"
echo ""
```

**Step 2: Make script executable**

Run: `chmod +x examples/azure/production/deploy.sh`

**Step 3: Commit**

```bash
git add examples/azure/production/deploy.sh
git commit -m "feat: add production deployment script"
```

---

## Phase 6: Documentation and Testing

### Task 16: Create production README

**Files:**
- Create: `examples/azure/production/README.md`

**Step 1: Create README (first half)**

Create `examples/azure/production/README.md`:

```markdown
# Production Azure Deployment

Production-ready deployment with VNet isolation, private endpoints, and managed identity authentication.

## Architecture

### Network Security
- **VNet Isolation**: All backend services in private subnets
- **Private Endpoints**: PostgreSQL, Storage, ACR accessible only via VNet
- **Service-Based Subnets**: Container Apps (/23), PostgreSQL (/24), Private Endpoints (/24)
- **Private DNS**: Automatic resolution for private endpoints

### Identity and Access
- **System-Assigned Managed Identity**: No client secrets required
- **RBAC in Bicep**: All permissions defined in infrastructure code
- **Roles**:
  - DICOM Data Owner (DICOM Service)
  - Storage Blob Data Contributor (Storage Account)
  - AcrPull (Container Registry)

### Infrastructure Components
- Azure Container Apps Environment with VNet integration
- PostgreSQL Flexible Server with VNet integration
- Storage Account with blob private endpoint
- Container Registry with registry private endpoint
- Healthcare Workspace + DICOM Service (public)
- Private DNS Zones (postgres, blob, ACR)
- Log Analytics Workspace

## Prerequisites

- Azure CLI installed and authenticated (`az login`)
- Docker Desktop running
- Bash shell (macOS/Linux)
- Azure subscription with required permissions

## Deployment

### Quick Start

```bash
# Clone repository
git clone https://github.com/yourusername/orthanc-dicomweb-oauth.git
cd orthanc-dicomweb-oauth/examples/azure/production

# Deploy
./deploy.sh
```

### Custom Configuration

```bash
# Set environment variables
export ENV_NAME="staging"  # or "production"
export LOCATION="eastus"   # or your preferred region

# Deploy
./deploy.sh
```

## Verification

### 1. Check Managed Identity

```bash
CONTAINER_APP_NAME="orthanc-production-app"
RG_NAME="rg-orthanc-production"

# Get managed identity principal ID
az containerapp show -n $CONTAINER_APP_NAME -g $RG_NAME \
  --query identity.principalId -o tsv
```

### 2. Verify Private Endpoints

```bash
# Check private endpoint IPs
az network private-endpoint list -g $RG_NAME --query "[].{Name:name, IP:customDnsConfigs[0].ipAddresses[0]}" -o table
```

### 3. Test DICOM Upload

```bash
CONTAINER_APP_URL=$(az containerapp show -n $CONTAINER_APP_NAME -g $RG_NAME --query properties.configuration.ingress.fqdn -o tsv)

# Upload test DICOM file
curl -u admin:PASSWORD -X POST "https://${CONTAINER_APP_URL}/instances" \
  --data-binary @test.dcm
```

## Security Features

- ✅ No public endpoints for PostgreSQL, Storage, ACR
- ✅ All backend traffic stays within VNet
- ✅ Managed identity (no client secrets)
- ✅ Private DNS for endpoint resolution
- ✅ TLS 1.2+ enforced on all services
- ✅ Storage public access disabled
- ✅ ACR admin user disabled

## Cost Optimization

Estimated monthly cost: **$150-200**

- Container Apps Environment: ~$50/month
- PostgreSQL B2s: ~$30/month
- Storage (Standard LRS): ~$20/month
- Container Registry (Basic): ~$5/month
- DICOM Service: ~$40/month
- VNet/Private Endpoints: ~$10/month

## Troubleshooting

### Issue: Container App can't pull image from ACR

**Solution**: Verify RBAC assignment
```bash
PRINCIPAL_ID=$(az containerapp show -n $CONTAINER_APP_NAME -g $RG_NAME --query identity.principalId -o tsv)
az role assignment list --assignee $PRINCIPAL_ID --scope $(az acr show -n $ACR_NAME -g $RG_NAME --query id -o tsv)
```

### Issue: Can't connect to PostgreSQL

**Solution**: Verify VNet integration
```bash
az postgres flexible-server show -n $POSTGRES_NAME -g $RG_NAME \
  --query network -o json
```

## Next Steps

- Add Application Insights for monitoring
- Enable zone redundancy for HA
- Add Application Gateway + WAF for external access
- Configure backup policies
- Set up CI/CD pipeline

## References

- [Design Document](../../docs/plans/2026-02-15-production-deployment-design.md)
- [Azure Container Apps Networking](https://learn.microsoft.com/azure/container-apps/networking)
- [Azure Private Endpoints](https://learn.microsoft.com/azure/private-link/private-endpoint-overview)
```

**Step 2: Commit README**

```bash
git add examples/azure/production/README.md
git commit -m "docs: add production deployment README"
```

---

### Task 17: Create SECURITY.md with best practices

**Files:**
- Create: `examples/azure/production/SECURITY.md`

**Step 1: Create SECURITY.md**

Create `examples/azure/production/SECURITY.md`:

```markdown
# Security Best Practices

This document outlines the security features and best practices for the production deployment.

## Network Security

### VNet Isolation
- All backend services deployed in private subnets
- No direct internet access to PostgreSQL, Storage, or Container Registry
- Container Apps Environment integrated with VNet

### Private Endpoints
- **PostgreSQL**: Accessible only via `10.0.2.x` private IP
- **Storage Account**: Blob service accessible via `10.0.3.x` private IP
- **Container Registry**: Registry service accessible via `10.0.3.x` private IP
- **DNS**: Automatic resolution via Private DNS zones

### Network Security Groups (Future Enhancement)
- Apply NSGs to restrict traffic between subnets
- Allow only necessary ports and protocols

## Identity and Access Management

### Managed Identity
- **System-Assigned**: Container App has automatic managed identity
- **No Secrets**: No client credentials stored or managed
- **Automatic Rotation**: Azure handles credential rotation

### RBAC Assignments
- **Least Privilege**: Only required roles assigned
- **DICOM Data Owner**: For DICOM Service read/write
- **Storage Blob Data Contributor**: For blob storage access
- **AcrPull**: For pulling container images only

### Secret Management
- **Orthanc Password**: Stored as Container App secret
- **PostgreSQL Password**: Stored as Container App secret
- **Auto-Generated**: Passwords generated during deployment

## Data Protection

### Encryption at Rest
- Storage Account: Microsoft-managed keys
- PostgreSQL: Microsoft-managed keys
- Container Registry: Microsoft-managed keys

### Encryption in Transit
- TLS 1.2+ enforced on all services
- HTTPS only for Container App ingress
- PostgreSQL requires SSL connections

### Data Retention
- Blob Storage: 7-day soft delete enabled
- PostgreSQL: Point-in-time restore supported (7 days)
- Logs: Retained in Log Analytics (30 days default)

## Monitoring and Auditing

### Logging
- Container App logs to Log Analytics
- PostgreSQL logs to Log Analytics
- Storage Account diagnostic logs enabled

### Metrics
- Prometheus metrics exposed by Orthanc plugin
- Azure Monitor metrics for all services

### Alerts (Future Enhancement)
- Failed authentication attempts
- Unusual network traffic patterns
- Resource utilization thresholds

## Compliance

### HIPAA Compliance Considerations
- Enable audit logging for all services
- Implement data loss prevention policies
- Regular access reviews
- Encrypt data at rest and in transit
- Business Associate Agreement (BAA) with Azure

### Data Residency
- All data stays in selected Azure region
- No cross-region replication by default
- Consider geo-redundancy for HA

## Hardening Checklist

- [ ] Enable Azure Defender for all services
- [ ] Configure Network Security Groups
- [ ] Enable firewall rules on Storage Account
- [ ] Enable AAD authentication for PostgreSQL
- [ ] Rotate Orthanc admin password regularly
- [ ] Review and minimize RBAC assignments
- [ ] Enable diagnostic logging for all resources
- [ ] Configure alert rules for security events
- [ ] Implement backup and disaster recovery
- [ ] Regular security assessments

## Vulnerability Management

### Container Image Scanning
- Enable Azure Defender for Container Registry
- Scan images before deployment
- Regular base image updates

### Dependency Management
- Keep Python dependencies updated
- Monitor for security advisories
- Use Dependabot or similar tools

### Patch Management
- Container Apps: Automatic platform updates
- PostgreSQL: Managed service handles patching
- Application: Regular image rebuilds

## Incident Response

### Security Event Detection
1. Monitor Container App logs for authentication failures
2. Check Azure Activity Log for unauthorized changes
3. Review Network Watcher logs for suspicious traffic

### Response Procedures
1. Isolate affected resources
2. Rotate credentials if compromised
3. Review and revoke RBAC assignments if needed
4. Analyze logs to determine scope
5. Document and report incident

## References

- [Azure Security Best Practices](https://learn.microsoft.com/azure/security/fundamentals/best-practices-and-patterns)
- [Container Apps Security](https://learn.microsoft.com/azure/container-apps/security)
- [HIPAA on Azure](https://learn.microsoft.com/azure/compliance/offerings/offering-hipaa-us)
```

**Step 2: Commit SECURITY.md**

```bash
git add examples/azure/production/SECURITY.md
git commit -m "docs: add security best practices"
```

---

### Task 18: Run full test suite to ensure no regressions

**Step 1: Run all tests**

Run: `pytest tests/ -v --cov=src --cov-report=term-missing`
Expected: All tests PASS, coverage >85%

**Step 2: Fix any failing tests**

(If tests fail, fix them before proceeding)

**Step 3: Commit test fixes**

```bash
git add tests/
git commit -m "test: fix regressions from production changes"
```

---

### Task 19: Update project root README

**Files:**
- Modify: `README.md`

**Step 1: Add production deployment section**

Add to `README.md` (find deployment section):

```markdown
## Deployment Options

### Azure Quickstart (15 minutes)
Perfect for demos and testing. Single command deployment.

```bash
cd examples/azure/quickstart
./deploy.sh
```

**Features**: Public endpoints, client credentials, simple setup

[Quickstart Guide →](examples/azure/quickstart/README.md)

### Azure Production (20 minutes)
Production-ready with enterprise security patterns.

```bash
cd examples/azure/production
./deploy.sh
```

**Features**: VNet isolation, private endpoints, managed identity, zero secrets

[Production Guide →](examples/azure/production/README.md)
```

**Step 2: Commit README update**

```bash
git add README.md
git commit -m "docs: add production deployment option to README"
```

---

## Final Steps

### Task 20: Create comprehensive commit for all work

**Step 1: Verify all files are committed**

Run: `git status`
Expected: Working tree clean

**Step 2: Tag the release (optional)**

```bash
git tag -a v1.0.0-production -m "Production deployment with VNet and managed identity"
git push origin v1.0.0-production
```

**Step 3: Push all changes**

```bash
git push origin main
```

---

## Success Criteria Checklist

- [ ] All tests pass
- [ ] Python managed identity provider implemented
- [ ] Network module with VNet and subnets created
- [ ] Private DNS zones module created
- [ ] Private endpoint module created
- [ ] Storage module with private endpoint created
- [ ] Container Registry module with private endpoint created
- [ ] Container App module with managed identity created
- [ ] RBAC assignments module created
- [ ] Main orchestration Bicep template created
- [ ] Deployment script created and executable
- [ ] Production README created
- [ ] SECURITY.md created
- [ ] Project README updated
- [ ] No regressions in existing tests
- [ ] Documentation complete

---

## Estimated Timeline

- **Phase 1** (Python Plugin): 1-2 days
- **Phase 2** (Network Bicep): 1 day
- **Phase 3** (Storage/Registry Bicep): 1 day
- **Phase 4** (Container App/RBAC Bicep): 1 day
- **Phase 5** (Orchestration/Deploy Script): 1 day
- **Phase 6** (Documentation/Testing): 1 day

**Total**: 6-8 days

---

## Notes

- Follow TDD strictly for Python code
- Verify Bicep syntax after each module
- Commit frequently (after each task)
- Test thoroughly before moving to next phase
- Document any deviations from plan
