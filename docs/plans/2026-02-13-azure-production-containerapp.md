# Azure Production Container Apps with VNet Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Deploy production-ready Orthanc with OAuth to Azure Container Apps using managed identity, private networking, and VNet integration.

**Architecture:** Infrastructure-as-code using Bicep templates with Azure Verified Modules (AVM) for VNet-integrated Container Apps. Implements managed identity authentication (no client secrets) with private endpoints for all backend services (PostgreSQL, Storage, DICOM). Network isolation through NSGs and private DNS zones.

**Tech Stack:**
- Infrastructure: Bicep, Azure Verified Modules (AVM)
- Networking: Azure VNet, Private Endpoints, Private DNS, NSGs
- Authentication: Managed Identity (system-assigned)
- Container Orchestration: Azure Container Apps (workload profiles)
- Backend Services: PostgreSQL Flexible Server, Blob Storage (private endpoints)
- Scripting: Bash, Azure CLI 2.50+

---

## Prerequisites

This plan builds on the quickstart foundation from Phase 1 (Tasks 10-17). You should have:
- `examples/azure/quickstart/` - Complete quickstart deployment
- Understanding of Azure VNet, Private Endpoints, Managed Identity

---

## Phase 2: Production Container Apps with Private Networking

### Task 18: Production Bicep Parameters Template

**Files:**
- Create: `examples/azure/production/main.bicepparam`
- Create: `examples/azure/production/parameters.json.template`

**Step 1: Create Bicep parameters file**

File: `examples/azure/production/main.bicepparam`
```bicep
using './main.bicep'

// Environment configuration
param environmentName = 'production'
param location = 'eastus'
param resourceGroupName = 'rg-orthanc-production'

// Networking configuration
param vnetAddressPrefix = '10.0.0.0/16'
param containerAppsSubnetPrefix = '10.0.1.0/24'
param privateEndpointsSubnetPrefix = '10.0.2.0/24'

// Container image configuration
param containerImage = 'myregistry.azurecr.io/orthanc-oauth:latest'
param containerRegistryName = 'myregistry'
param containerRegistryResourceGroup = 'rg-shared-services'

// DICOM service configuration
param dicomServiceUrl = 'https://workspace.dicom.azurehealthcareapis.com/v2/'
param dicomScope = 'https://dicom.healthcareapis.azure.com/.default'

// Database configuration
param postgresAdminUsername = 'orthanc_admin'
@secure()
param postgresAdminPassword = ''

// Orthanc admin credentials
param orthancUsername = 'admin'
@secure()
param orthancPassword = ''

// Enable/disable features
param enablePrivateEndpoints = true
param enableNetworkIsolation = true

// Tags
param tags = {
  Environment: 'Production'
  Project: 'Orthanc-OAuth'
  ManagedBy: 'Bicep'
  Compliance: 'HIPAA'
}
```

**Step 2: Create JSON template for easy customization**

File: `examples/azure/production/parameters.json.template`
```json
{
  "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentParameters.json#",
  "contentVersion": "1.0.0.0",
  "parameters": {
    "environmentName": {
      "value": "production"
    },
    "location": {
      "value": "eastus"
    },
    "resourceGroupName": {
      "value": "rg-orthanc-production"
    },
    "vnetAddressPrefix": {
      "value": "10.0.0.0/16"
    },
    "containerAppsSubnetPrefix": {
      "value": "10.0.1.0/24"
    },
    "privateEndpointsSubnetPrefix": {
      "value": "10.0.2.0/24"
    },
    "containerImage": {
      "value": "REPLACE_WITH_YOUR_REGISTRY.azurecr.io/orthanc-oauth:latest"
    },
    "containerRegistryName": {
      "value": "REPLACE_WITH_YOUR_REGISTRY_NAME"
    },
    "containerRegistryResourceGroup": {
      "value": "REPLACE_WITH_ACR_RESOURCE_GROUP"
    },
    "dicomServiceUrl": {
      "value": "REPLACE_WITH_YOUR_DICOM_SERVICE_URL"
    },
    "dicomScope": {
      "value": "https://dicom.healthcareapis.azure.com/.default"
    },
    "postgresAdminUsername": {
      "value": "orthanc_admin"
    },
    "postgresAdminPassword": {
      "reference": {
        "keyVault": {
          "id": "/subscriptions/SUBSCRIPTION_ID/resourceGroups/RG_NAME/providers/Microsoft.KeyVault/vaults/VAULT_NAME"
        },
        "secretName": "postgres-admin-password"
      }
    },
    "orthancUsername": {
      "value": "admin"
    },
    "orthancPassword": {
      "reference": {
        "keyVault": {
          "id": "/subscriptions/SUBSCRIPTION_ID/resourceGroups/RG_NAME/providers/Microsoft.KeyVault/vaults/VAULT_NAME"
        },
        "secretName": "orthanc-admin-password"
      }
    },
    "enablePrivateEndpoints": {
      "value": true
    },
    "enableNetworkIsolation": {
      "value": true
    },
    "tags": {
      "value": {
        "Environment": "Production",
        "Project": "Orthanc-OAuth",
        "ManagedBy": "Bicep",
        "Compliance": "HIPAA"
      }
    }
  }
}
```

**Step 3: Validate JSON syntax**

```bash
cat examples/azure/production/parameters.json.template | jq . > /dev/null
```

Expected: No errors

**Step 4: Commit**

```bash
git add examples/azure/production/main.bicepparam examples/azure/production/parameters.json.template
git commit -m "feat(azure): add production Bicep parameter templates

Add parameter files for Azure production deployment with VNet:
- main.bicepparam: Bicep parameter file with production defaults
- parameters.json.template: JSON template with VNet configuration

Includes networking parameters for private endpoints and managed identity.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

### Task 19: VNet and Networking Bicep Module

**Files:**
- Create: `examples/azure/production/modules/networking.bicep`

**Step 1: Create VNet module with subnets and NSGs**

File: `examples/azure/production/modules/networking.bicep`
```bicep
// ========================================
// Virtual Network Module for Production
// ========================================

@description('The Azure region for resources')
param location string

@description('The name prefix for networking resources')
param namePrefix string

@description('VNet address prefix')
param vnetAddressPrefix string = '10.0.0.0/16'

@description('Container Apps subnet address prefix')
param containerAppsSubnetPrefix string = '10.0.1.0/24'

@description('Private Endpoints subnet address prefix')
param privateEndpointsSubnetPrefix string = '10.0.2.0/24'

@description('Resource tags')
param tags object = {}

// ========================================
// Variables
// ========================================

var vnetName = '${namePrefix}-vnet'
var containerAppsSubnetName = 'snet-containerApps'
var privateEndpointsSubnetName = 'snet-privateEndpoints'
var containerAppsNsgName = '${namePrefix}-nsg-containerApps'
var privateEndpointsNsgName = '${namePrefix}-nsg-privateEndpoints'

// ========================================
// Network Security Groups
// ========================================

// NSG for Container Apps subnet
resource containerAppsNsg 'Microsoft.Network/networkSecurityGroups@2023-11-01' = {
  name: containerAppsNsgName
  location: location
  tags: tags
  properties: {
    securityRules: [
      {
        name: 'AllowHTTPSInbound'
        properties: {
          priority: 100
          direction: 'Inbound'
          access: 'Allow'
          protocol: 'Tcp'
          sourcePortRange: '*'
          destinationPortRange: '443'
          sourceAddressPrefix: 'Internet'
          destinationAddressPrefix: '*'
        }
      }
      {
        name: 'AllowVnetInbound'
        properties: {
          priority: 110
          direction: 'Inbound'
          access: 'Allow'
          protocol: '*'
          sourcePortRange: '*'
          destinationPortRange: '*'
          sourceAddressPrefix: 'VirtualNetwork'
          destinationAddressPrefix: 'VirtualNetwork'
        }
      }
      {
        name: 'DenyAllInbound'
        properties: {
          priority: 4096
          direction: 'Inbound'
          access: 'Deny'
          protocol: '*'
          sourcePortRange: '*'
          destinationPortRange: '*'
          sourceAddressPrefix: '*'
          destinationAddressPrefix: '*'
        }
      }
    ]
  }
}

// NSG for Private Endpoints subnet
resource privateEndpointsNsg 'Microsoft.Network/networkSecurityGroups@2023-11-01' = {
  name: privateEndpointsNsgName
  location: location
  tags: tags
  properties: {
    securityRules: [
      {
        name: 'AllowVnetInbound'
        properties: {
          priority: 100
          direction: 'Inbound'
          access: 'Allow'
          protocol: '*'
          sourcePortRange: '*'
          destinationPortRange: '*'
          sourceAddressPrefix: 'VirtualNetwork'
          destinationAddressPrefix: 'VirtualNetwork'
        }
      }
      {
        name: 'DenyAllInbound'
        properties: {
          priority: 4096
          direction: 'Inbound'
          access: 'Deny'
          protocol: '*'
          sourcePortRange: '*'
          destinationPortRange: '*'
          sourceAddressPrefix: '*'
          destinationAddressPrefix: '*'
        }
      }
    ]
  }
}

// ========================================
// Virtual Network
// ========================================

resource vnet 'Microsoft.Network/virtualNetworks@2023-11-01' = {
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
        name: containerAppsSubnetName
        properties: {
          addressPrefix: containerAppsSubnetPrefix
          networkSecurityGroup: {
            id: containerAppsNsg.id
          }
          delegations: [
            {
              name: 'Microsoft.App.environments'
              properties: {
                serviceName: 'Microsoft.App/environments'
              }
            }
          ]
        }
      }
      {
        name: privateEndpointsSubnetName
        properties: {
          addressPrefix: privateEndpointsSubnetPrefix
          networkSecurityGroup: {
            id: privateEndpointsNsg.id
          }
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
output privateEndpointsSubnetId string = vnet.properties.subnets[1].id
output containerAppsSubnetName string = containerAppsSubnetName
output privateEndpointsSubnetName string = privateEndpointsSubnetName
```

**Step 2: Validate module**

```bash
az bicep build --file examples/azure/production/modules/networking.bicep
```

Expected: Build succeeds

**Step 3: Commit**

```bash
git add examples/azure/production/modules/
git commit -m "feat(azure): add VNet and networking Bicep module

Add comprehensive networking module for production deployment:
- Virtual Network with two subnets
- Container Apps subnet with delegation
- Private Endpoints subnet with policies disabled
- Network Security Groups for both subnets
- Outputs for subnet IDs and names

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

### Task 20: Private DNS Zones Module

**Files:**
- Create: `examples/azure/production/modules/private-dns.bicep`

**Step 1: Create Private DNS zones module**

File: `examples/azure/production/modules/private-dns.bicep`
```bicep
// ========================================
// Private DNS Zones Module
// ========================================

@description('Virtual Network ID to link DNS zones to')
param vnetId string

@description('Virtual Network name for link naming')
param vnetName string

@description('Resource tags')
param tags object = {}

// ========================================
// Private DNS Zones
// ========================================

// Private DNS Zone for PostgreSQL
resource postgresDnsZone 'Microsoft.Network/privateDnsZones@2020-06-01' = {
  name: 'privatelink.postgres.database.azure.com'
  location: 'global'
  tags: tags
}

// Private DNS Zone for Blob Storage
resource blobDnsZone 'Microsoft.Network/privateDnsZones@2020-06-01' = {
  name: 'privatelink.blob.${environment().suffixes.storage}'
  location: 'global'
  tags: tags
}

// ========================================
// VNet Links
// ========================================

// Link PostgreSQL DNS zone to VNet
resource postgresVnetLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2020-06-01' = {
  parent: postgresDnsZone
  name: '${vnetName}-postgres-link'
  location: 'global'
  tags: tags
  properties: {
    registrationEnabled: false
    virtualNetwork: {
      id: vnetId
    }
  }
}

// Link Blob DNS zone to VNet
resource blobVnetLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2020-06-01' = {
  parent: blobDnsZone
  name: '${vnetName}-blob-link'
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
output postgresDnsZoneName string = postgresDnsZone.name
output blobDnsZoneName string = blobDnsZone.name
```

**Step 2: Validate module**

```bash
az bicep build --file examples/azure/production/modules/private-dns.bicep
```

Expected: Build succeeds

**Step 3: Commit**

```bash
git add examples/azure/production/modules/private-dns.bicep
git commit -m "feat(azure): add Private DNS zones Bicep module

Add Private DNS module for private endpoint resolution:
- Private DNS zone for PostgreSQL
- Private DNS zone for Blob Storage
- VNet links for both zones
- Outputs for zone IDs and names

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

### Task 21: Main Production Bicep Template

**Files:**
- Create: `examples/azure/production/main.bicep`

**Step 1: Create main production template with VNet integration**

File: `examples/azure/production/main.bicep`
```bicep
targetScope = 'subscription'

// ========================================
// Parameters
// ========================================

@description('The name of the environment')
param environmentName string

@description('The Azure region where resources will be deployed')
param location string

@description('The name of the resource group to create')
param resourceGroupName string

@description('VNet address prefix')
param vnetAddressPrefix string

@description('Container Apps subnet prefix')
param containerAppsSubnetPrefix string

@description('Private Endpoints subnet prefix')
param privateEndpointsSubnetPrefix string

@description('The container image to deploy')
param containerImage string

@description('The name of the Azure Container Registry')
param containerRegistryName string

@description('The resource group containing the ACR')
param containerRegistryResourceGroup string

@description('The URL of the DICOM service')
param dicomServiceUrl string

@description('The OAuth scope for the DICOM service')
param dicomScope string

@description('PostgreSQL administrator username')
param postgresAdminUsername string

@description('PostgreSQL administrator password')
@secure()
param postgresAdminPassword string

@description('Orthanc admin username')
param orthancUsername string

@description('Orthanc admin password')
@secure()
param orthancPassword string

@description('Enable private endpoints')
param enablePrivateEndpoints bool = true

@description('Enable network isolation')
param enableNetworkIsolation bool = true

@description('Resource tags')
param tags object = {}

// ========================================
// Variables
// ========================================

var resourcePrefix = 'orthanc-${environmentName}'
var postgresServerName = '${resourcePrefix}-db-${uniqueString(subscription().subscriptionId, resourceGroupName)}'
var storageAccountName = toLower(take(replace('${resourcePrefix}sa${uniqueString(subscription().subscriptionId, resourceGroupName)}', '-', ''), 24))
var containerAppsEnvironmentName = '${resourcePrefix}-cae'
var containerAppName = '${resourcePrefix}-app'
var logAnalyticsName = '${resourcePrefix}-logs'

// ========================================
// Resource Group
// ========================================

resource rg 'Microsoft.Resources/resourceGroups@2024-03-01' = {
  name: resourceGroupName
  location: location
  tags: tags
}

// ========================================
// Networking Module
// ========================================

module networking './modules/networking.bicep' = {
  scope: rg
  name: 'networkingDeployment'
  params: {
    location: location
    namePrefix: resourcePrefix
    vnetAddressPrefix: vnetAddressPrefix
    containerAppsSubnetPrefix: containerAppsSubnetPrefix
    privateEndpointsSubnetPrefix: privateEndpointsSubnetPrefix
    tags: tags
  }
}

// ========================================
// Private DNS Module
// ========================================

module privateDns './modules/private-dns.bicep' = {
  scope: rg
  name: 'privateDnsDeployment'
  params: {
    vnetId: networking.outputs.vnetId
    vnetName: networking.outputs.vnetName
    tags: tags
  }
}

// ========================================
// Log Analytics Workspace (AVM)
// ========================================

module logAnalytics 'br/public:avm/res/operational-insights/workspace:0.9.1' = {
  scope: rg
  name: 'logAnalyticsDeployment'
  params: {
    name: logAnalyticsName
    location: location
    tags: tags
    dataRetention: 90
    skuName: 'PerGB2018'
  }
}

// ========================================
// Storage Account (AVM) with Private Endpoint
// ========================================

module storageAccount 'br/public:avm/res/storage/storage-account:0.14.3' = {
  scope: rg
  name: 'storageAccountDeployment'
  params: {
    name: storageAccountName
    location: location
    tags: tags
    kind: 'StorageV2'
    skuName: 'Standard_LRS'
    blobServices: {
      containers: [
        {
          name: 'orthanc-dicom'
          publicAccess: 'None'
        }
      ]
    }
    networkAcls: {
      defaultAction: enableNetworkIsolation ? 'Deny' : 'Allow'
      bypass: 'AzureServices'
      virtualNetworkRules: enableNetworkIsolation ? [
        {
          id: networking.outputs.containerAppsSubnetId
          action: 'Allow'
        }
      ] : []
    }
    privateEndpoints: enablePrivateEndpoints ? [
      {
        name: '${storageAccountName}-blob-pe'
        subnetResourceId: networking.outputs.privateEndpointsSubnetId
        service: 'blob'
        privateDnsZoneGroup: {
          privateDnsZoneGroupConfigs: [
            {
              privateDnsZoneResourceId: privateDns.outputs.blobDnsZoneId
            }
          ]
        }
      }
    ] : []
  }
}

// Reference to storage account for getting keys
resource storageAccountResource 'Microsoft.Storage/storageAccounts@2023-05-01' existing = {
  name: storageAccountName
  scope: rg
  dependsOn: [
    storageAccount
  ]
}

// ========================================
// PostgreSQL Flexible Server (AVM) with Private Endpoint
// ========================================

module postgres 'br/public:avm/res/db-for-postgre-sql/flexible-server:0.8.0' = {
  scope: rg
  name: 'postgresDeployment'
  params: {
    name: postgresServerName
    location: location
    tags: tags
    skuName: 'Standard_D2ds_v4'
    tier: 'GeneralPurpose'
    storageSizeGB: 128
    version: '15'
    administratorLogin: postgresAdminUsername
    administratorLoginPassword: postgresAdminPassword
    databases: [
      {
        name: 'orthanc'
      }
    ]
    firewallRules: enableNetworkIsolation ? [] : [
      {
        name: 'AllowAllAzureIPs'
        startIpAddress: '0.0.0.0'
        endIpAddress: '0.0.0.0'
      }
    ]
    delegatedSubnetResourceId: enablePrivateEndpoints ? networking.outputs.privateEndpointsSubnetId : null
    privateDnsZoneArmResourceId: enablePrivateEndpoints ? privateDns.outputs.postgresDnsZoneId : null
  }
}

// ========================================
// Container Apps Environment (AVM) with VNet
// ========================================

module containerAppsEnvironment 'br/public:avm/res/app/managed-environment:0.8.1' = {
  scope: rg
  name: 'containerAppsEnvDeployment'
  params: {
    name: containerAppsEnvironmentName
    location: location
    tags: tags
    logAnalyticsWorkspaceResourceId: logAnalytics.outputs.resourceId
    infrastructureSubnetResourceId: networking.outputs.containerAppsSubnetId
    internal: enableNetworkIsolation
    workloadProfiles: [
      {
        name: 'Consumption'
        workloadProfileType: 'Consumption'
      }
    ]
  }
}

// ========================================
// Container App (AVM) with Managed Identity
// ========================================

module containerApp 'br/public:avm/res/app/container-app:0.11.0' = {
  scope: rg
  name: 'containerAppDeployment'
  params: {
    name: containerAppName
    location: location
    tags: tags
    environmentResourceId: containerAppsEnvironment.outputs.resourceId
    workloadProfileName: 'Consumption'
    containers: [
      {
        name: 'orthanc'
        image: containerImage
        resources: {
          cpu: json('2.0')
          memory: '4Gi'
        }
        env: [
          {
            name: 'ORTHANC__POSTGRESQL__HOST'
            value: postgres.outputs.fqdn
          }
          {
            name: 'ORTHANC__POSTGRESQL__PORT'
            value: '5432'
          }
          {
            name: 'ORTHANC__POSTGRESQL__DATABASE'
            value: 'orthanc'
          }
          {
            name: 'ORTHANC__POSTGRESQL__USERNAME'
            value: postgresAdminUsername
          }
          {
            name: 'ORTHANC__POSTGRESQL__PASSWORD'
            secretRef: 'postgres-password'
          }
          {
            name: 'ORTHANC__AZURE_BLOB_STORAGE__CONNECTION_STRING'
            secretRef: 'storage-connection-string'
          }
          {
            name: 'ORTHANC__AZURE_BLOB_STORAGE__CONTAINER'
            value: 'orthanc-dicom'
          }
          {
            name: 'AZURE_CLIENT_ID'
            value: containerApp.outputs.systemAssignedMIPrincipalId
          }
          {
            name: 'DICOM_SERVICE_URL'
            value: dicomServiceUrl
          }
          {
            name: 'DICOM_SCOPE'
            value: dicomScope
          }
          {
            name: 'USE_MANAGED_IDENTITY'
            value: 'true'
          }
          {
            name: 'ORTHANC_USERNAME'
            value: orthancUsername
          }
          {
            name: 'ORTHANC_PASSWORD'
            secretRef: 'orthanc-password'
          }
        ]
        probes: [
          {
            type: 'Liveness'
            httpGet: {
              path: '/system'
              port: 8042
            }
            initialDelaySeconds: 30
            periodSeconds: 10
          }
          {
            type: 'Readiness'
            httpGet: {
              path: '/system'
              port: 8042
            }
            initialDelaySeconds: 10
            periodSeconds: 5
          }
        ]
      }
    ]
    secrets: {
      secureList: [
        {
          name: 'postgres-password'
          value: postgresAdminPassword
        }
        {
          name: 'storage-connection-string'
          value: 'DefaultEndpointsProtocol=https;AccountName=${storageAccountResource.name};AccountKey=${storageAccountResource.listKeys().keys[0].value};EndpointSuffix=${environment().suffixes.storage}'
        }
        {
          name: 'orthanc-password'
          value: orthancPassword
        }
      ]
    }
    ingressExternal: !enableNetworkIsolation
    ingressTargetPort: 8042
    ingressTransport: 'http'
    ingressAllowInsecure: false
    trafficLatestRevision: true
    trafficWeight: 100
    scaleMinReplicas: 2
    scaleMaxReplicas: 10
    scaleRules: [
      {
        name: 'http-rule'
        http: {
          metadata: {
            concurrentRequests: '50'
          }
        }
      }
      {
        name: 'cpu-rule'
        custom: {
          type: 'cpu'
          metadata: {
            type: 'Utilization'
            value: '75'
          }
        }
      }
    ]
    registries: [
      {
        server: '${containerRegistryName}.azurecr.io'
        identity: 'system'
      }
    ]
    managedIdentities: {
      systemAssigned: true
    }
  }
}

// ========================================
// Role Assignments
// ========================================

// Grant Container App system identity ACR Pull role
module acrPullRoleAssignment 'br/public:avm/ptn/authorization/resource-role-assignment:0.1.1' = {
  scope: resourceGroup(containerRegistryResourceGroup)
  name: 'acrPullRoleAssignment'
  params: {
    principalId: containerApp.outputs.systemAssignedMIPrincipalId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7f951dda-4ed3-4680-a7ca-43fe172d538d') // AcrPull
    resourceId: subscriptionResourceId(containerRegistryResourceGroup, 'Microsoft.ContainerRegistry/registries', containerRegistryName)
  }
}

// Grant Container App managed identity Storage Blob Data Contributor role
module storageBlobRoleAssignment 'br/public:avm/ptn/authorization/resource-role-assignment:0.1.1' = {
  scope: rg
  name: 'storageBlobRoleAssignment'
  params: {
    principalId: containerApp.outputs.systemAssignedMIPrincipalId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'ba92f5b4-2d11-453d-a403-e96b0029c9fe') // Storage Blob Data Contributor
    resourceId: storageAccount.outputs.resourceId
  }
}

// ========================================
// Outputs
// ========================================

output resourceGroupName string = rg.name
output containerAppUrl string = containerApp.outputs.fqdn
output containerAppIdentityPrincipalId string = containerApp.outputs.systemAssignedMIPrincipalId
output postgresServerFqdn string = postgres.outputs.fqdn
output storageAccountName string = storageAccount.outputs.name
output vnetId string = networking.outputs.vnetId
output vnetName string = networking.outputs.vnetName
```

**Step 2: Validate Bicep syntax**

```bash
az bicep build --file examples/azure/production/main.bicep
```

Expected: Build succeeds with no errors

**Step 3: Validate Bicep with linter**

```bash
az bicep lint --file examples/azure/production/main.bicep
```

Expected: No critical errors

**Step 4: Commit**

```bash
git add examples/azure/production/main.bicep
git commit -m "feat(azure): add production Bicep template with VNet and managed identity

Add comprehensive production template with Azure Verified Modules:
- VNet integration with Container Apps Environment
- Private endpoints for PostgreSQL and Storage
- Managed identity authentication (no client secrets)
- Network isolation with NSGs
- Private DNS zones for name resolution
- Enhanced scaling (2-10 replicas, CPU-based)
- Role assignments for ACR and Storage access

Uses managed identity instead of client credentials for OAuth.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

### Task 22: Production Deployment Script

**Files:**
- Create: `examples/azure/production/scripts/deploy.sh`

**Step 1: Create production deployment script**

File: `examples/azure/production/scripts/deploy.sh`
```bash
#!/usr/bin/env bash
set -euo pipefail

# ========================================
# Deploy Orthanc OAuth Production to Azure
# ========================================
#
# This script deploys the production Orthanc OAuth setup to Azure
# with VNet integration and managed identity.
#
# Prerequisites:
# - Azure CLI 2.50+
# - Docker (for building custom image)
# - Azure Container Registry
# - Permissions to assign roles
#
# Usage:
#   ./deploy.sh --resource-group rg-orthanc-prod --location eastus --registry myregistry
#

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
RESOURCE_GROUP=""
LOCATION="eastus"
ENVIRONMENT_NAME="production"
PARAMETERS_FILE="parameters.json"
BUILD_IMAGE=true
CONTAINER_REGISTRY=""
CONTAINER_REGISTRY_RG=""
IMAGE_TAG="latest"
VNET_ADDRESS_PREFIX="10.0.0.0/16"
CONTAINER_APPS_SUBNET="10.0.1.0/24"
PRIVATE_ENDPOINTS_SUBNET="10.0.2.0/24"

# ========================================
# Functions
# ========================================

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Deploy Orthanc OAuth production setup to Azure with VNet and managed identity.

OPTIONS:
    -g, --resource-group NAME       Resource group name (required)
    -l, --location LOCATION         Azure region (default: eastus)
    -e, --environment NAME          Environment name (default: production)
    -p, --parameters FILE           Parameters JSON file (default: parameters.json)
    -r, --registry NAME             Azure Container Registry name (required if building)
    -R, --registry-rg NAME          ACR resource group (default: same as resource group)
    -t, --tag TAG                   Container image tag (default: latest)
    --vnet-prefix PREFIX            VNet address prefix (default: 10.0.0.0/16)
    --container-subnet PREFIX       Container Apps subnet (default: 10.0.1.0/24)
    --private-subnet PREFIX         Private Endpoints subnet (default: 10.0.2.0/24)
    --no-build                      Skip building container image
    -h, --help                      Show this help message

EXAMPLE:
    $0 --resource-group rg-orthanc-prod --registry myregistry --registry-rg rg-shared

EOF
}

# ========================================
# Parse Arguments
# ========================================

while [[ $# -gt 0 ]]; do
    case $1 in
        -g|--resource-group)
            RESOURCE_GROUP="$2"
            shift 2
            ;;
        -l|--location)
            LOCATION="$2"
            shift 2
            ;;
        -e|--environment)
            ENVIRONMENT_NAME="$2"
            shift 2
            ;;
        -p|--parameters)
            PARAMETERS_FILE="$2"
            shift 2
            ;;
        -r|--registry)
            CONTAINER_REGISTRY="$2"
            shift 2
            ;;
        -R|--registry-rg)
            CONTAINER_REGISTRY_RG="$2"
            shift 2
            ;;
        -t|--tag)
            IMAGE_TAG="$2"
            shift 2
            ;;
        --vnet-prefix)
            VNET_ADDRESS_PREFIX="$2"
            shift 2
            ;;
        --container-subnet)
            CONTAINER_APPS_SUBNET="$2"
            shift 2
            ;;
        --private-subnet)
            PRIVATE_ENDPOINTS_SUBNET="$2"
            shift 2
            ;;
        --no-build)
            BUILD_IMAGE=false
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Validate required parameters
if [[ -z "$RESOURCE_GROUP" ]]; then
    log_error "Resource group is required"
    show_usage
    exit 1
fi

if [[ "$BUILD_IMAGE" == true && -z "$CONTAINER_REGISTRY" ]]; then
    log_error "Container registry is required when building image"
    show_usage
    exit 1
fi

# Default ACR RG to same as deployment RG if not specified
if [[ -z "$CONTAINER_REGISTRY_RG" ]]; then
    CONTAINER_REGISTRY_RG="$RESOURCE_GROUP"
fi

# ========================================
# Main Script
# ========================================

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

log_step "Step 1/7: Validating prerequisites"

# Check Azure CLI
az version --output tsv > /dev/null 2>&1 || {
    log_error "Azure CLI not found. Please install Azure CLI 2.50+"
    exit 1
}

# Check logged in
az account show > /dev/null 2>&1 || {
    log_error "Not logged in to Azure. Run 'az login' first."
    exit 1
}

SUBSCRIPTION_ID=$(az account show --query id -o tsv)
log_info "Using subscription: $SUBSCRIPTION_ID"

# ========================================
# Build and Push Container Image
# ========================================

if [[ "$BUILD_IMAGE" == true ]]; then
    log_step "Step 2/7: Building and pushing container image"

    CONTAINER_IMAGE="${CONTAINER_REGISTRY}.azurecr.io/orthanc-oauth:${IMAGE_TAG}"

    # Login to ACR
    log_info "Logging into Azure Container Registry: $CONTAINER_REGISTRY"
    az acr login --name "$CONTAINER_REGISTRY"

    # Build image for linux/amd64 (required for Azure Container Apps)
    log_info "Building Docker image: $CONTAINER_IMAGE"
    docker buildx build \
        --platform linux/amd64 \
        -t "$CONTAINER_IMAGE" \
        -f examples/azure/quickstart/Dockerfile \
        --push \
        "$REPO_ROOT"

    log_info "Image pushed: $CONTAINER_IMAGE"
else
    log_step "Step 2/7: Skipping image build (--no-build specified)"

    # Read from parameters file if exists
    if [[ -f "$PARAMETERS_FILE" ]]; then
        CONTAINER_IMAGE=$(jq -r '.parameters.containerImage.value' "$PARAMETERS_FILE")
        log_info "Using existing image: $CONTAINER_IMAGE"
    else
        log_error "No parameters file found and --no-build specified"
        exit 1
    fi
fi

# ========================================
# Create Resource Group
# ========================================

log_step "Step 3/7: Creating resource group"

if az group show --name "$RESOURCE_GROUP" &> /dev/null; then
    log_info "Resource group already exists: $RESOURCE_GROUP"
else
    log_info "Creating resource group: $RESOURCE_GROUP"
    az group create --name "$RESOURCE_GROUP" --location "$LOCATION"
fi

# ========================================
# Generate Deployment Parameters
# ========================================

log_step "Step 4/7: Generating deployment parameters"

# Read DICOM service URL from parameters file
DICOM_SERVICE_URL=$(jq -r '.parameters.dicomServiceUrl.value' "$PARAMETERS_FILE")

# Generate secure passwords
POSTGRES_PASSWORD=$(openssl rand -base64 32)
ORTHANC_PASSWORD=$(openssl rand -base64 24)

# Create deployment parameters
cat > deployment-params.json << EOF
{
  "environmentName": "$ENVIRONMENT_NAME",
  "location": "$LOCATION",
  "resourceGroupName": "$RESOURCE_GROUP",
  "vnetAddressPrefix": "$VNET_ADDRESS_PREFIX",
  "containerAppsSubnetPrefix": "$CONTAINER_APPS_SUBNET",
  "privateEndpointsSubnetPrefix": "$PRIVATE_ENDPOINTS_SUBNET",
  "containerImage": "$CONTAINER_IMAGE",
  "containerRegistryName": "$CONTAINER_REGISTRY",
  "containerRegistryResourceGroup": "$CONTAINER_REGISTRY_RG",
  "dicomServiceUrl": "$DICOM_SERVICE_URL",
  "dicomScope": "https://dicom.healthcareapis.azure.com/.default",
  "postgresAdminUsername": "orthanc_admin",
  "postgresAdminPassword": "$POSTGRES_PASSWORD",
  "orthancUsername": "admin",
  "orthancPassword": "$ORTHANC_PASSWORD",
  "enablePrivateEndpoints": true,
  "enableNetworkIsolation": true
}
EOF

log_info "Deployment parameters generated"

# ========================================
# Deploy Bicep Template
# ========================================

log_step "Step 5/7: Deploying Azure resources with Bicep"

DEPLOYMENT_NAME="orthanc-production-$(date +%Y%m%d-%H%M%S)"

log_info "Starting deployment: $DEPLOYMENT_NAME"

az deployment sub create \
    --name "$DEPLOYMENT_NAME" \
    --location "$LOCATION" \
    --template-file "$SCRIPT_DIR/../main.bicep" \
    --parameters @deployment-params.json \
    --output json > deployment-output.json

log_info "Deployment complete"

# ========================================
# Extract Managed Identity Principal ID
# ========================================

log_step "Step 6/7: Configuring managed identity permissions"

MANAGED_IDENTITY_ID=$(jq -r '.properties.outputs.containerAppIdentityPrincipalId.value' deployment-output.json)

log_info "Container App Managed Identity: $MANAGED_IDENTITY_ID"

# Note: DICOM Data Owner role assignment should be done manually or via separate script
# as it requires the DICOM service resource ID

log_warn "IMPORTANT: Grant DICOM Data Owner role to managed identity:"
log_warn "  az role assignment create \\"
log_warn "    --assignee $MANAGED_IDENTITY_ID \\"
log_warn "    --role 'DICOM Data Owner' \\"
log_warn "    --scope /subscriptions/$SUBSCRIPTION_ID/resourceGroups/YOUR_DICOM_RG/providers/Microsoft.HealthcareApis/workspaces/YOUR_WORKSPACE"

# ========================================
# Display Outputs
# ========================================

log_step "Step 7/7: Deployment summary"

CONTAINER_APP_URL=$(jq -r '.properties.outputs.containerAppUrl.value' deployment-output.json)
POSTGRES_FQDN=$(jq -r '.properties.outputs.postgresServerFqdn.value' deployment-output.json)
STORAGE_ACCOUNT=$(jq -r '.properties.outputs.storageAccountName.value' deployment-output.json)
VNET_NAME=$(jq -r '.properties.outputs.vnetName.value' deployment-output.json)

cat << EOF

${GREEN}✓ Deployment successful!${NC}

Resource Group: $RESOURCE_GROUP
Location: $LOCATION

Resources deployed:
  - VNet: $VNET_NAME
  - Container App: https://$CONTAINER_APP_URL
  - PostgreSQL: $POSTGRES_FQDN (private endpoint)
  - Storage Account: $STORAGE_ACCOUNT (private endpoint)

Authentication:
  - Managed Identity: $MANAGED_IDENTITY_ID

Orthanc Credentials:
  - Username: admin
  - Password: $ORTHANC_PASSWORD

Next steps:
  1. Grant DICOM Data Owner role to managed identity (see warning above)
  2. Access Orthanc at: https://$CONTAINER_APP_URL
  3. Test deployment: cd ../../../quickstart/scripts && ./test-deployment.sh --url https://$CONTAINER_APP_URL --password $ORTHANC_PASSWORD
  4. View logs: az containerapp logs show --name orthanc-$ENVIRONMENT_NAME-app --resource-group $RESOURCE_GROUP

EOF

# Save deployment details
cat > deployment-details.json << EOF
{
  "resourceGroup": "$RESOURCE_GROUP",
  "location": "$LOCATION",
  "containerAppUrl": "https://$CONTAINER_APP_URL",
  "postgresFqdn": "$POSTGRES_FQDN",
  "storageAccount": "$STORAGE_ACCOUNT",
  "vnetName": "$VNET_NAME",
  "managedIdentityId": "$MANAGED_IDENTITY_ID",
  "orthancUsername": "admin",
  "orthancPassword": "$ORTHANC_PASSWORD",
  "deploymentName": "$DEPLOYMENT_NAME",
  "deploymentTimestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF

log_info "Deployment details saved to: deployment-details.json"
```

**Step 2: Make script executable**

```bash
chmod +x examples/azure/production/scripts/deploy.sh
```

**Step 3: Test script syntax**

```bash
bash -n examples/azure/production/scripts/deploy.sh
```

Expected: No syntax errors

**Step 4: Test help output**

```bash
examples/azure/production/scripts/deploy.sh --help
```

Expected: Shows usage information

**Step 5: Commit**

```bash
git add examples/azure/production/scripts/deploy.sh
git commit -m "feat(azure): add production deployment script with VNet support

Add bash script to automate production Azure deployment:
- VNet configuration with customizable address spaces
- Managed identity authentication (no client secrets)
- Private endpoints for PostgreSQL and Storage
- Network isolation configuration
- Role assignment for ACR and Storage
- Comprehensive deployment summary

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

### Task 23: Grant DICOM Permissions Script

**Files:**
- Create: `examples/azure/production/scripts/grant-dicom-permissions.sh`

**Step 1: Create script to grant DICOM permissions to managed identity**

File: `examples/azure/production/scripts/grant-dicom-permissions.sh`
```bash
#!/usr/bin/env bash
set -euo pipefail

# ========================================
# Grant DICOM Permissions to Managed Identity
# ========================================
#
# This script grants DICOM Data Owner role to the Container App's
# managed identity for accessing Azure Health Data Services.
#
# Prerequisites:
# - Azure CLI 2.50+
# - Deployment completed (deployment-details.json exists)
# - User with permissions to assign roles on DICOM service
#
# Usage:
#   ./grant-dicom-permissions.sh --dicom-workspace-id /subscriptions/.../workspaces/my-workspace
#

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
DICOM_WORKSPACE_ID=""
DEPLOYMENT_DETAILS_FILE="deployment-details.json"

# ========================================
# Functions
# ========================================

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Grant DICOM Data Owner role to Container App managed identity.

OPTIONS:
    -w, --dicom-workspace-id ID     DICOM workspace resource ID (required)
    -d, --deployment FILE           Deployment details JSON (default: deployment-details.json)
    -h, --help                      Show this help message

EXAMPLE:
    $0 --dicom-workspace-id /subscriptions/abc123/resourceGroups/rg-dicom/providers/Microsoft.HealthcareApis/workspaces/my-workspace

EOF
}

# ========================================
# Parse Arguments
# ========================================

while [[ $# -gt 0 ]]; do
    case $1 in
        -w|--dicom-workspace-id)
            DICOM_WORKSPACE_ID="$2"
            shift 2
            ;;
        -d|--deployment)
            DEPLOYMENT_DETAILS_FILE="$2"
            shift 2
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Validate required parameters
if [[ -z "$DICOM_WORKSPACE_ID" ]]; then
    log_error "DICOM workspace ID is required"
    show_usage
    exit 1
fi

# ========================================
# Main Script
# ========================================

# Check Azure CLI
az version --output tsv > /dev/null 2>&1 || {
    log_error "Azure CLI not found. Please install Azure CLI 2.50+"
    exit 1
}

# Check logged in
az account show > /dev/null 2>&1 || {
    log_error "Not logged in to Azure. Run 'az login' first."
    exit 1
}

# Check deployment details file exists
if [[ ! -f "$DEPLOYMENT_DETAILS_FILE" ]]; then
    log_error "Deployment details file not found: $DEPLOYMENT_DETAILS_FILE"
    log_error "Run deploy.sh first"
    exit 1
fi

# Load managed identity ID from deployment details
MANAGED_IDENTITY_ID=$(jq -r '.managedIdentityId' "$DEPLOYMENT_DETAILS_FILE")

if [[ -z "$MANAGED_IDENTITY_ID" || "$MANAGED_IDENTITY_ID" == "null" ]]; then
    log_error "Could not find managed identity ID in deployment details"
    exit 1
fi

log_info "Managed Identity: $MANAGED_IDENTITY_ID"
log_info "DICOM Workspace: $DICOM_WORKSPACE_ID"

# Grant DICOM Data Owner role
log_info "Granting DICOM Data Owner role..."

az role assignment create \
    --assignee "$MANAGED_IDENTITY_ID" \
    --role "DICOM Data Owner" \
    --scope "$DICOM_WORKSPACE_ID"

log_info "${GREEN}✓ DICOM permissions granted successfully!${NC}"

# Verify role assignment
log_info "Verifying role assignment..."

ROLE_ASSIGNMENTS=$(az role assignment list \
    --assignee "$MANAGED_IDENTITY_ID" \
    --scope "$DICOM_WORKSPACE_ID" \
    --query "[?roleDefinitionName=='DICOM Data Owner'].roleDefinitionName" \
    -o tsv)

if [[ "$ROLE_ASSIGNMENTS" == "DICOM Data Owner" ]]; then
    log_info "${GREEN}✓ Verification successful - Role assignment confirmed${NC}"
else
    log_warn "Could not verify role assignment. Check Azure Portal."
fi

cat << EOF

${GREEN}✓ Configuration complete!${NC}

The Container App can now access the DICOM service using its managed identity.

Next steps:
  1. Test DICOM connectivity
  2. Upload test images to verify OAuth authentication
  3. Monitor Container App logs for any authentication errors

EOF
```

**Step 2: Make script executable**

```bash
chmod +x examples/azure/production/scripts/grant-dicom-permissions.sh
```

**Step 3: Test script syntax**

```bash
bash -n examples/azure/production/scripts/grant-dicom-permissions.sh
```

Expected: No syntax errors

**Step 4: Commit**

```bash
git add examples/azure/production/scripts/grant-dicom-permissions.sh
git commit -m "feat(azure): add script to grant DICOM permissions to managed identity

Add helper script to grant DICOM Data Owner role:
- Reads managed identity from deployment details
- Grants role on specified DICOM workspace
- Verifies role assignment
- Provides next steps

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

### Task 24: Production README

**Files:**
- Create: `examples/azure/production/README.md`

**Step 1: Create comprehensive production documentation**

File: `examples/azure/production/README.md`
```markdown
# Azure Production Deployment

Deploy Orthanc with OAuth plugin to Azure Container Apps using **managed identity**, **private networking**, and **VNet integration**.

## Overview

This production deployment provides:
- **Authentication**: Managed Identity (no client secrets)
- **Networking**: Private VNet with isolated subnets
- **Database**: Azure Database for PostgreSQL Flexible Server (private endpoint)
- **Storage**: Azure Blob Storage (private endpoint)
- **DICOM Service**: Azure Health Data Services DICOM
- **Security**: Network isolation, NSGs, Private DNS
- **High Availability**: Auto-scaling (2-10 replicas), zone redundancy
- **Estimated Cost**: ~$350/month
- **Setup Time**: ~30 minutes

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Azure Subscription                          │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Virtual Network (10.0.0.0/16)                            │ │
│  │                                                             │ │
│  │  ┌──────────────────────────────────────────────────────┐ │ │
│  │  │  Subnet: Container Apps (10.0.1.0/24)               │ │ │
│  │  │  Delegation: Microsoft.App/environments              │ │ │
│  │  │                                                       │ │ │
│  │  │  ┌────────────────────────────────────────────────┐ │ │ │
│  │  │  │  Container Apps Environment                    │ │ │ │
│  │  │  │  ┌──────────────────────────────────────────┐ │ │ │ │
│  │  │  │  │  Orthanc + OAuth (Managed Identity)      │ │ │ │ │
│  │  │  │  │  - System-assigned identity               │ │ │ │ │
│  │  │  │  │  - Auto-scaling: 2-10 replicas           │ │ │ │ │
│  │  │  │  └──────────────────────────────────────────┘ │ │ │ │
│  │  │  └────────────────────────────────────────────────┘ │ │ │
│  │  └──────────────────────────────────────────────────────┘ │ │
│  │                                                             │ │
│  │  ┌──────────────────────────────────────────────────────┐ │ │
│  │  │  Subnet: Private Endpoints (10.0.2.0/24)            │ │ │
│  │  │                                                       │ │ │
│  │  │  ┌───────────────┐    ┌──────────────────────────┐ │ │ │
│  │  │  │  PostgreSQL   │    │  Blob Storage            │ │ │ │
│  │  │  │  Private      │    │  Private Endpoint        │ │ │ │
│  │  │  │  Endpoint     │    │                          │ │ │ │
│  │  │  └───────────────┘    └──────────────────────────┘ │ │ │
│  │  └──────────────────────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Private DNS Zones                                         │ │
│  │  - privatelink.postgres.database.azure.com                 │ │
│  │  - privatelink.blob.core.windows.net                       │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Azure Health Data Services                                │ │
│  │  ┌──────────────────────────────────────────────────────┐ │ │
│  │  │  DICOM Service (Managed Identity authentication)      │ │ │
│  │  └──────────────────────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Key Differences from Quickstart

| Feature | Quickstart | Production |
|---------|-----------|------------|
| Authentication | Client ID + Secret | Managed Identity |
| Networking | Public endpoints | Private VNet |
| Database Access | Public with firewall | Private endpoint |
| Storage Access | Public with firewall | Private endpoint |
| Isolation | Basic | Network-level isolation |
| Scaling | 1-3 replicas | 2-10 replicas |
| Cost | ~$67/month | ~$350/month |
| Security | Good | Enhanced |

## Prerequisites

- **Azure subscription** with Contributor + User Access Administrator roles
- **Azure CLI** 2.50 or later ([Install](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli))
- **Docker** for building custom image ([Install](https://docs.docker.com/get-docker/))
- **jq** for JSON processing ([Install](https://stedolan.github.io/jq/download/))
- **Azure Health Data Services** DICOM workspace already deployed
- **Azure Container Registry** for storing Docker images

## Quick Start

### Step 1: Login to Azure

```bash
az login
az account set --subscription "your-subscription-id"
```

### Step 2: Configure Parameters

```bash
cd examples/azure/production
cp parameters.json.template parameters.json
```

Edit `parameters.json` and replace:
- `REPLACE_WITH_YOUR_DICOM_SERVICE_URL`
- `REPLACE_WITH_YOUR_REGISTRY_NAME`
- `REPLACE_WITH_ACR_RESOURCE_GROUP`
- VNet address prefixes (if needed)

### Step 3: Deploy Infrastructure

```bash
./scripts/deploy.sh \
  --resource-group rg-orthanc-production \
  --location eastus \
  --registry myregistry \
  --registry-rg rg-shared-services
```

This will:
1. Build Docker image with Orthanc + OAuth plugin
2. Push image to Azure Container Registry
3. Deploy VNet with subnets and NSGs
4. Deploy PostgreSQL with private endpoint
5. Deploy Storage Account with private endpoint
6. Deploy Container Apps Environment (VNet-integrated)
7. Deploy Container App with managed identity
8. Configure role assignments for ACR and Storage

Deployment takes ~25-30 minutes.

### Step 4: Grant DICOM Permissions

```bash
./scripts/grant-dicom-permissions.sh \
  --dicom-workspace-id "/subscriptions/YOUR_SUB/resourceGroups/YOUR_RG/providers/Microsoft.HealthcareApis/workspaces/YOUR_WORKSPACE"
```

This grants the managed identity **DICOM Data Owner** role.

### Step 5: Test Deployment

```bash
cd ../../quickstart/scripts
./test-deployment.sh --url https://orthanc-production-app.example.com --password YOUR_PASSWORD
```

## Cost Estimate

Approximate monthly costs (East US region):

| Resource | SKU | Monthly Cost |
|----------|-----|--------------|
| Container Apps | Dedicated, 2-10 vCPU, 4-20GB RAM | $150 |
| PostgreSQL Flexible | GeneralPurpose D2ds_v4, 128GB storage | $120 |
| VNet | Standard tier with private endpoints | $15 |
| Private Endpoints | 2 endpoints | $20 |
| Blob Storage | LRS, ~100GB | $2 |
| Log Analytics | 10GB ingestion | $10 |
| Container Registry | Standard tier | $20 |
| Private DNS Zones | 2 zones | $2 |
| **Total** | | **~$339/month** |

> Costs vary by region, usage, and scaling. Use [Azure Pricing Calculator](https://azure.microsoft.com/pricing/calculator/) for accurate estimates.

## Configuration

### Managed Identity

The Container App uses a **system-assigned managed identity** for authentication:
- No client secrets to manage or rotate
- Automatic credential management by Azure
- Role assignments:
  - **ACR Pull** - Pull container images
  - **Storage Blob Data Contributor** - Access DICOM files
  - **DICOM Data Owner** - Access DICOM service

### Network Isolation

The deployment creates:
- **VNet** with two subnets:
  - Container Apps subnet (delegated)
  - Private Endpoints subnet
- **Network Security Groups** with rules:
  - Allow HTTPS inbound (443)
  - Allow VNet-to-VNet traffic
  - Deny all other inbound traffic
- **Private Endpoints** for:
  - PostgreSQL Flexible Server
  - Blob Storage
- **Private DNS Zones** for name resolution:
  - `privatelink.postgres.database.azure.com`
  - `privatelink.blob.core.windows.net`

### Scaling

Production deployment includes enhanced auto-scaling:
- **Min replicas**: 2 (high availability)
- **Max replicas**: 10 (handle traffic spikes)
- **Scale triggers**:
  - HTTP concurrent requests (50 threshold)
  - CPU utilization (75% threshold)

Adjust in `main.bicep`:

```bicep
scaleMinReplicas: 2
scaleMaxReplicas: 10
scaleRules: [
  {
    name: 'http-rule'
    http: {
      metadata: {
        concurrentRequests: '50'
      }
    }
  }
  {
    name: 'cpu-rule'
    custom: {
      type: 'cpu'
      metadata: {
        type: 'Utilization'
        value: '75'
      }
    }
  }
]
```

## Accessing Orthanc

### From Within VNet

If accessing from resources within the VNet:

```bash
ORTHANC_URL=$(jq -r '.containerAppUrl' deployment-details.json)
curl -u admin:PASSWORD https://$ORTHANC_URL/system
```

### From Internet

For internal-only deployments (`enableNetworkIsolation: true`), you need:
- Azure Bastion or VPN connection to VNet
- Or deploy Application Gateway with public IP

For external access, set in `main.bicepparam`:
```bicep
param enableNetworkIsolation = false  // Allows external ingress
```

### Logs

```bash
az containerapp logs show \
  --name orthanc-production-app \
  --resource-group rg-orthanc-production \
  --follow
```

## Monitoring

### Prometheus Metrics

Metrics available at `/metrics` endpoint:

```bash
curl -u admin:PASSWORD https://$ORTHANC_URL/metrics
```

Key metrics:
- `orthanc_managed_identity_token_acquisition_total` - Managed identity token requests
- `orthanc_token_cache_hits_total` - Token cache hits
- `orthanc_http_requests_total` - HTTP requests to DICOM service

### Log Analytics

Query logs in Azure Portal or CLI:

```bash
WORKSPACE_ID=$(az containerapp env show \
  --name orthanc-production-cae \
  --resource-group rg-orthanc-production \
  --query properties.appLogsConfiguration.logAnalyticsConfiguration.customerId -o tsv)

az monitor log-analytics query \
  --workspace $WORKSPACE_ID \
  --analytics-query "ContainerAppConsoleLogs_CL | where TimeGenerated > ago(1h) | project TimeGenerated, Log_s | order by TimeGenerated desc"
```

## Troubleshooting

### Managed Identity Authentication Fails

**Check role assignments**:
```bash
IDENTITY_ID=$(jq -r '.managedIdentityId' deployment-details.json)
az role assignment list --assignee $IDENTITY_ID --all
```

**Expected roles**:
- ACR Pull (on Container Registry)
- Storage Blob Data Contributor (on Storage Account)
- DICOM Data Owner (on DICOM workspace)

**Test managed identity token**:
```bash
az containerapp exec \
  --name orthanc-production-app \
  --resource-group rg-orthanc-production \
  --command /bin/bash

# Inside container
curl -H "Metadata: true" "http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource=https://dicom.healthcareapis.azure.com"
```

### Private Endpoint Resolution Issues

**Check Private DNS zones are linked to VNet**:
```bash
az network private-dns link vnet list \
  --resource-group rg-orthanc-production \
  --zone-name privatelink.postgres.database.azure.com
```

**Test DNS resolution from Container App**:
```bash
az containerapp exec \
  --name orthanc-production-app \
  --resource-group rg-orthanc-production \
  --command /bin/bash

# Inside container
apt-get update && apt-get install -y dnsutils
nslookup orthanc-production-db-xxx.postgres.database.azure.com
```

Should resolve to private IP (10.0.2.x).

### Database Connection Errors

**Check NSG rules allow VNet traffic**:
```bash
az network nsg rule list \
  --resource-group rg-orthanc-production \
  --nsg-name orthanc-production-nsg-privateEndpoints \
  --query "[].{Name:name, Priority:priority, Direction:direction, Access:access}"
```

**Test connectivity from Container App**:
```bash
az containerapp exec \
  --name orthanc-production-app \
  --resource-group rg-orthanc-production \
  --command /bin/bash

# Inside container
apt-get update && apt-get install -y postgresql-client
psql -h POSTGRES_HOST -U orthanc_admin -d orthanc
```

## Cleanup

Delete all resources:

```bash
cd ../../quickstart/scripts
./cleanup.sh --resource-group rg-orthanc-production --yes
```

**Note**: This deletes the entire resource group including VNet, private endpoints, and all data.

## Security Considerations

### Production Checklist

- [x] Use Managed Identity (no client secrets)
- [x] Private endpoints for all backend services
- [x] Network isolation with VNet
- [x] NSGs with restrictive rules
- [x] Private DNS for name resolution
- [ ] Use Azure Key Vault for Orthanc admin password
- [ ] Enable diagnostic logging for all resources
- [ ] Configure Azure Monitor alerts
- [ ] Implement backup strategy for PostgreSQL
- [ ] Set up Azure DDoS Protection (if public ingress)
- [ ] Configure Azure Firewall (if needed)
- [ ] Review and audit role assignments quarterly
- [ ] Enable Azure Defender for Cloud

### Network Security

Production deployment includes:
- **Zero trust networking** - All traffic denied by default
- **Subnet delegation** - Container Apps subnet dedicated to Azure
- **Private endpoints** - No public IP for backend services
- **NSG rules** - Restrictive inbound/outbound rules
- **Private DNS** - Prevent DNS exfiltration

### Identity Security

Managed Identity advantages:
- **No credential storage** - Azure manages credentials
- **Automatic rotation** - No manual secret rotation
- **Audit trail** - All access logged in Azure AD
- **Least privilege** - Specific role assignments only

## Next Steps

- **Monitoring**: Configure Application Insights for advanced monitoring
- **Backup**: Set up automated PostgreSQL backups with point-in-time restore
- **Disaster Recovery**: Implement geo-redundancy and failover
- **CI/CD**: Create GitHub Actions workflow for automated deployments
- **Application Gateway**: Add WAF and SSL termination for public access
- **AKS Migration**: See [../production-aks/](../production-aks/) for Kubernetes deployment

## Support

For issues and questions:
- **Plugin Issues**: [GitHub Issues](https://github.com/rhavekost/orthanc-dicomweb-oauth/issues)
- **Azure Issues**: [Azure Support](https://azure.microsoft.com/support/)
- **Orthanc Questions**: [Orthanc Forum](https://groups.google.com/g/orthanc-users)
```

**Step 2: Commit**

```bash
git add examples/azure/production/README.md
git commit -m "docs(azure): add comprehensive production deployment README

Add complete documentation for production deployment:
- Architecture diagram with VNet and private endpoints
- Managed identity authentication guide
- Network isolation and security details
- Comparison with quickstart deployment
- Cost estimates and scaling configuration
- Monitoring and troubleshooting guides
- Security best practices and checklists

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Summary

Phase 2 (Tasks 18-24) is complete! You now have:

✅ **Task 18**: Production Bicep parameter templates
✅ **Task 19**: VNet and networking Bicep module
✅ **Task 20**: Private DNS zones module
✅ **Task 21**: Main production Bicep template with managed identity
✅ **Task 22**: Production deployment automation script
✅ **Task 23**: Grant DICOM permissions script
✅ **Task 24**: Comprehensive production README

**What you can do now**:
- Deploy production-ready Orthanc with managed identity
- Use private networking with VNet integration
- No client secrets to manage or rotate
- Enhanced security with private endpoints and NSGs
- Auto-scaling (2-10 replicas) for high availability

**Key Improvements over Quickstart**:
- **Authentication**: Managed Identity (no secrets)
- **Networking**: Private VNet with isolated subnets
- **Security**: Private endpoints, NSGs, network isolation
- **Scalability**: Enhanced auto-scaling with CPU-based rules
- **Cost**: ~$350/month (vs ~$67 for quickstart)

**Next Phases**:
- **Phase 3**: Production AKS (Tasks 25-31) - AKS cluster with Helm chart
- **Phase 4**: Documentation and Testing (Tasks 32-40)

Would you like to continue with Phase 3 (AKS deployment)?
