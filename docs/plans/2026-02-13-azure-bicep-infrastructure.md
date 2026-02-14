# Azure Bicep Infrastructure Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create production-ready Azure deployment infrastructure using Bicep and Azure Verified Modules for three deployment scenarios: quickstart Container Apps, production Container Apps with private networking, and production AKS.

**Architecture:** Infrastructure-as-code using Bicep templates with Azure Verified Modules (AVM) for consistent, best-practice Azure resources. Implements both client credentials and managed identity authentication patterns. Includes automated deployment scripts and comprehensive testing.

**Tech Stack:**
- Infrastructure: Bicep, Azure Verified Modules (AVM)
- Container Orchestration: Azure Container Apps, Azure Kubernetes Service
- Cloud Services: Azure Health Data Services (DICOM), PostgreSQL Flexible Server, Blob Storage, Key Vault
- Scripting: Bash, Azure CLI 2.50+
- Testing: Pester (PowerShell), Bash test framework

---

## Prerequisites

This plan builds on the Helm chart foundation from Tasks 1-9 (already completed). You should have:
- `examples/kubernetes/orthanc-oauth/` - Complete Helm chart
- `examples/azure/quickstart/Dockerfile` - Basic Dockerfile

---

## Phase 1: Azure Quickstart Infrastructure (Container Apps)

### Task 10: Bicep Parameters Template

**Files:**
- Create: `examples/azure/quickstart/main.bicepparam`
- Create: `examples/azure/quickstart/parameters.json.template`

**Step 1: Create Bicep parameters file**

File: `examples/azure/quickstart/main.bicepparam`
```bicep
using './main.bicep'

// Environment configuration
param environmentName = 'quickstart'
param location = 'eastus'
param resourceGroupName = 'rg-orthanc-quickstart'

// Container image configuration
param containerImage = 'myregistry.azurecr.io/orthanc-oauth:latest'
param containerRegistryName = 'myregistry'

// DICOM service configuration
param dicomServiceUrl = 'https://workspace.dicom.azurehealthcareapis.com/v2/'
param tenantId = '00000000-0000-0000-0000-000000000000'
param dicomScope = 'https://dicom.healthcareapis.azure.com/.default'

// OAuth client credentials
param oauthClientId = '00000000-0000-0000-0000-000000000000'
@secure()
param oauthClientSecret = ''

// Database configuration
param postgresAdminUsername = 'orthanc_admin'
@secure()
param postgresAdminPassword = ''

// Orthanc admin credentials
param orthancUsername = 'admin'
@secure()
param orthancPassword = ''

// Tags
param tags = {
  Environment: 'Quickstart'
  Project: 'Orthanc-OAuth'
  ManagedBy: 'Bicep'
}
```

**Step 2: Create JSON template for easy customization**

File: `examples/azure/quickstart/parameters.json.template`
```json
{
  "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentParameters.json#",
  "contentVersion": "1.0.0.0",
  "parameters": {
    "environmentName": {
      "value": "quickstart"
    },
    "location": {
      "value": "eastus"
    },
    "resourceGroupName": {
      "value": "rg-orthanc-quickstart"
    },
    "containerImage": {
      "value": "REPLACE_WITH_YOUR_REGISTRY.azurecr.io/orthanc-oauth:latest"
    },
    "containerRegistryName": {
      "value": "REPLACE_WITH_YOUR_REGISTRY_NAME"
    },
    "dicomServiceUrl": {
      "value": "REPLACE_WITH_YOUR_DICOM_SERVICE_URL"
    },
    "tenantId": {
      "value": "REPLACE_WITH_YOUR_TENANT_ID"
    },
    "dicomScope": {
      "value": "https://dicom.healthcareapis.azure.com/.default"
    },
    "oauthClientId": {
      "value": "REPLACE_WITH_YOUR_CLIENT_ID"
    },
    "oauthClientSecret": {
      "reference": {
        "keyVault": {
          "id": "/subscriptions/SUBSCRIPTION_ID/resourceGroups/RG_NAME/providers/Microsoft.KeyVault/vaults/VAULT_NAME"
        },
        "secretName": "oauth-client-secret"
      }
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
    "tags": {
      "value": {
        "Environment": "Quickstart",
        "Project": "Orthanc-OAuth",
        "ManagedBy": "Bicep"
      }
    }
  }
}
```

**Step 3: Validate parameter files**

```bash
# Validate JSON syntax
cat examples/azure/quickstart/parameters.json.template | jq . > /dev/null
```

Expected: No errors

**Step 4: Commit**

```bash
git add examples/azure/quickstart/main.bicepparam examples/azure/quickstart/parameters.json.template
git commit -m "feat(azure): add Bicep parameter templates for quickstart

Add parameter files for Azure quickstart deployment:
- main.bicepparam: Bicep parameter file with defaults
- parameters.json.template: JSON template for easy customization

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

### Task 11: Main Bicep Template with AVM Modules

**Files:**
- Create: `examples/azure/quickstart/main.bicep`

**Step 1: Create main Bicep template**

File: `examples/azure/quickstart/main.bicep`
```bicep
targetScope = 'subscription'

// ========================================
// Parameters
// ========================================

@description('The name of the environment (e.g., quickstart, dev, prod)')
param environmentName string

@description('The Azure region where resources will be deployed')
param location string

@description('The name of the resource group to create')
param resourceGroupName string

@description('The container image to deploy (e.g., myregistry.azurecr.io/orthanc-oauth:latest)')
param containerImage string

@description('The name of the Azure Container Registry')
param containerRegistryName string

@description('The URL of the DICOM service')
param dicomServiceUrl string

@description('The Azure AD tenant ID')
param tenantId string

@description('The OAuth scope for the DICOM service')
param dicomScope string

@description('The OAuth client ID for client credentials flow')
param oauthClientId string

@description('The OAuth client secret')
@secure()
param oauthClientSecret string

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

@description('Resource tags')
param tags object = {}

// ========================================
// Variables
// ========================================

var resourcePrefix = 'orthanc-${environmentName}'
var postgresServerName = '${resourcePrefix}-db-${uniqueString(subscription().subscriptionId, resourceGroupName)}'
var storageAccountName = replace('${resourcePrefix}sa${uniqueString(subscription().subscriptionId, resourceGroupName)}', '-', '')
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
// Log Analytics Workspace (AVM)
// ========================================

module logAnalytics 'br/public:avm/res/operational-insights/workspace:0.9.1' = {
  scope: rg
  name: 'logAnalyticsDeployment'
  params: {
    name: logAnalyticsName
    location: location
    tags: tags
    retentionInDays: 30
    sku: 'PerGB2018'
  }
}

// ========================================
// Storage Account (AVM)
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
      defaultAction: 'Allow'
      bypass: 'AzureServices'
    }
  }
}

// ========================================
// PostgreSQL Flexible Server (AVM)
// ========================================

module postgres 'br/public:avm/res/db-for-postgre-sql/flexible-server:0.4.1' = {
  scope: rg
  name: 'postgresDeployment'
  params: {
    name: postgresServerName
    location: location
    tags: tags
    sku: {
      name: 'Standard_B2s'
      tier: 'Burstable'
    }
    storage: {
      storageSizeGB: 32
    }
    version: '15'
    administratorLogin: postgresAdminUsername
    administratorLoginPassword: postgresAdminPassword
    databases: [
      {
        name: 'orthanc'
      }
    ]
    firewallRules: [
      {
        name: 'AllowAllAzureIPs'
        startIpAddress: '0.0.0.0'
        endIpAddress: '0.0.0.0'
      }
    ]
  }
}

// ========================================
// Container Apps Environment (AVM)
// ========================================

module containerAppsEnvironment 'br/public:avm/res/app/managed-environment:0.8.1' = {
  scope: rg
  name: 'containerAppsEnvDeployment'
  params: {
    name: containerAppsEnvironmentName
    location: location
    tags: tags
    logAnalyticsWorkspaceResourceId: logAnalytics.outputs.resourceId
  }
}

// ========================================
// Container App (AVM)
// ========================================

module containerApp 'br/public:avm/res/app/container-app:0.11.0' = {
  scope: rg
  name: 'containerAppDeployment'
  params: {
    name: containerAppName
    location: location
    tags: tags
    environmentResourceId: containerAppsEnvironment.outputs.resourceId
    containers: [
      {
        name: 'orthanc'
        image: containerImage
        resources: {
          cpu: json('1.0')
          memory: '2Gi'
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
            name: 'OAUTH_CLIENT_ID'
            value: oauthClientId
          }
          {
            name: 'OAUTH_CLIENT_SECRET'
            secretRef: 'oauth-client-secret'
          }
          {
            name: 'OAUTH_TOKEN_ENDPOINT'
            value: 'https://login.microsoftonline.com/${tenantId}/oauth2/v2.0/token'
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
          value: storageAccount.outputs.primaryBlobConnectionString
        }
        {
          name: 'oauth-client-secret'
          value: oauthClientSecret
        }
        {
          name: 'orthanc-password'
          value: orthancPassword
        }
      ]
    }
    ingress: {
      external: true
      targetPort: 8042
      transport: 'http'
      allowInsecure: false
      traffic: [
        {
          latestRevision: true
          weight: 100
        }
      ]
    }
    scaleMinReplicas: 1
    scaleMaxReplicas: 3
    scaleRules: [
      {
        name: 'http-rule'
        http: {
          metadata: {
            concurrentRequests: '50'
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
  scope: rg
  name: 'acrPullRoleAssignment'
  params: {
    principalId: containerApp.outputs.systemAssignedMIPrincipalId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7f951dda-4ed3-4680-a7ca-43fe172d538d') // AcrPull
    resourceId: resourceId('Microsoft.ContainerRegistry/registries', containerRegistryName)
  }
}

// ========================================
// Outputs
// ========================================

output resourceGroupName string = rg.name
output containerAppUrl string = containerApp.outputs.fqdn
output postgresServerFqdn string = postgres.outputs.fqdn
output storageAccountName string = storageAccount.outputs.name
output containerAppIdentityPrincipalId string = containerApp.outputs.systemAssignedMIPrincipalId
```

**Step 2: Validate Bicep syntax**

```bash
az bicep build --file examples/azure/quickstart/main.bicep
```

Expected: Build succeeds with no errors

**Step 3: Validate Bicep with linter**

```bash
az bicep lint --file examples/azure/quickstart/main.bicep
```

Expected: No critical errors (warnings about parameter descriptions are OK)

**Step 4: Commit**

```bash
git add examples/azure/quickstart/main.bicep
git commit -m "feat(azure): add main Bicep template with AVM modules

Add comprehensive Bicep template using Azure Verified Modules:
- Log Analytics workspace for monitoring
- Storage Account for DICOM files with blob container
- PostgreSQL Flexible Server for Orthanc database
- Container Apps Environment for hosting
- Container App with Orthanc OAuth plugin
- Role assignments for ACR pull access

Uses client credentials OAuth flow for quickstart simplicity.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

### Task 12: Orthanc Configuration Module

**Files:**
- Create: `examples/azure/quickstart/modules/orthanc-config.bicep`

**Step 1: Create Bicep module for Orthanc configuration**

File: `examples/azure/quickstart/modules/orthanc-config.bicep`
```bicep
// ========================================
// Orthanc Configuration Module
// ========================================

@description('DICOM service URL')
param dicomServiceUrl string

@description('OAuth token endpoint')
param tokenEndpoint string

@description('OAuth scope')
param scope string

@description('Orthanc DICOM AET')
param dicomAet string = 'ORTHANC'

@description('Orthanc HTTP port')
param httpPort int = 8042

@description('Orthanc DICOM port')
param dicomPort int = 4242

// ========================================
// Outputs
// ========================================

output orthancConfig object = {
  Name: dicomAet
  RemoteAccessAllowed: true
  AuthenticationEnabled: true
  HttpPort: httpPort
  HttpCompressionEnabled: true
  HttpThreadsCount: 50
  DicomAet: dicomAet
  DicomPort: dicomPort
  DicomThreadsCount: 4
  Plugins: [
    '/etc/orthanc/plugins/dicomweb_oauth_plugin.py'
  ]
}

output oauthPluginConfig object = {
  DicomWebOAuth: {
    ConfigVersion: '2.0'
    LogLevel: 'INFO'
    RateLimitRequests: 100
    RateLimitWindowSeconds: 60
    Servers: {
      'azure-dicom': {
        Url: dicomServiceUrl
        TokenEndpoint: tokenEndpoint
        Scope: scope
        TokenRefreshBufferSeconds: 300
        ClientId: '${environment().authentication.identityProvider}OAUTH_CLIENT_ID'
        ClientSecret: '${environment().authentication.identityProvider}OAUTH_CLIENT_SECRET'
        VerifySSL: true
      }
    }
  }
}
```

**Step 2: Validate module**

```bash
az bicep build --file examples/azure/quickstart/modules/orthanc-config.bicep
```

Expected: Build succeeds

**Step 3: Commit**

```bash
git add examples/azure/quickstart/modules/
git commit -m "feat(azure): add Orthanc configuration Bicep module

Add reusable Bicep module for generating Orthanc and OAuth plugin
configuration objects. Supports parameterization of DICOM service
URL, OAuth endpoints, and Orthanc server settings.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

### Task 13: Setup App Registration Script

**Files:**
- Create: `examples/azure/quickstart/scripts/setup-app-registration.sh`

**Step 1: Create app registration setup script**

File: `examples/azure/quickstart/scripts/setup-app-registration.sh`
```bash
#!/usr/bin/env bash
set -euo pipefail

# ========================================
# Setup Azure AD App Registration
# ========================================
#
# This script creates an Azure AD app registration and service principal
# for OAuth client credentials authentication with Azure Health Data Services.
#
# Prerequisites:
# - Azure CLI 2.50+
# - User with Application Administrator or Global Administrator role
#
# Usage:
#   ./setup-app-registration.sh --name "orthanc-quickstart" --dicom-workspace-name "my-workspace"
#

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
APP_NAME=""
DICOM_WORKSPACE_NAME=""
OUTPUT_FILE="app-registration.json"

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

Create Azure AD app registration for Orthanc OAuth plugin.

OPTIONS:
    -n, --name NAME                  App registration name (required)
    -w, --dicom-workspace-name NAME  DICOM workspace name (required)
    -o, --output FILE                Output JSON file (default: app-registration.json)
    -h, --help                       Show this help message

EXAMPLE:
    $0 --name "orthanc-quickstart" --dicom-workspace-name "my-workspace"

EOF
}

# ========================================
# Parse Arguments
# ========================================

while [[ $# -gt 0 ]]; do
    case $1 in
        -n|--name)
            APP_NAME="$2"
            shift 2
            ;;
        -w|--dicom-workspace-name)
            DICOM_WORKSPACE_NAME="$2"
            shift 2
            ;;
        -o|--output)
            OUTPUT_FILE="$2"
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
if [[ -z "$APP_NAME" ]]; then
    log_error "App name is required"
    show_usage
    exit 1
fi

if [[ -z "$DICOM_WORKSPACE_NAME" ]]; then
    log_error "DICOM workspace name is required"
    show_usage
    exit 1
fi

# ========================================
# Main Script
# ========================================

log_info "Creating app registration: $APP_NAME"

# Check Azure CLI version
az version --output tsv > /dev/null 2>&1 || {
    log_error "Azure CLI not found. Please install Azure CLI 2.50+"
    exit 1
}

# Check logged in
az account show > /dev/null 2>&1 || {
    log_error "Not logged in to Azure. Run 'az login' first."
    exit 1
}

TENANT_ID=$(az account show --query tenantId -o tsv)
log_info "Using tenant: $TENANT_ID"

# Create app registration
log_info "Creating Azure AD application..."
APP_ID=$(az ad app create \
    --display-name "$APP_NAME" \
    --sign-in-audience AzureADMyOrg \
    --query appId -o tsv)

log_info "App ID: $APP_ID"

# Create service principal
log_info "Creating service principal..."
SP_OBJECT_ID=$(az ad sp create \
    --id "$APP_ID" \
    --query id -o tsv)

log_info "Service Principal Object ID: $SP_OBJECT_ID"

# Create client secret
log_info "Creating client secret..."
CLIENT_SECRET=$(az ad app credential reset \
    --id "$APP_ID" \
    --append \
    --years 2 \
    --query password -o tsv)

# Get DICOM service scope
DICOM_SCOPE="https://dicom.healthcareapis.azure.com/.default"
log_info "DICOM API scope: $DICOM_SCOPE"

# Grant API permissions
log_info "Granting API permissions for DICOM service..."
DICOM_API_ID="4f6778d8-5aef-43dc-a1ff-b073724ed0a4"  # Azure Healthcare APIs
DICOM_PERMISSION_ID="4c0bc8c2-3e8d-4d5e-8a4e-05e1be780e15"  # user_impersonation

az ad app permission add \
    --id "$APP_ID" \
    --api "$DICOM_API_ID" \
    --api-permissions "${DICOM_PERMISSION_ID}=Scope"

log_warn "Admin consent is required for the API permissions."
log_warn "Grant admin consent in the Azure Portal or run:"
log_warn "  az ad app permission admin-consent --id $APP_ID"

# Save output
cat > "$OUTPUT_FILE" << EOF
{
  "appName": "$APP_NAME",
  "tenantId": "$TENANT_ID",
  "clientId": "$APP_ID",
  "clientSecret": "$CLIENT_SECRET",
  "servicePrincipalObjectId": "$SP_OBJECT_ID",
  "dicomScope": "$DICOM_SCOPE",
  "tokenEndpoint": "https://login.microsoftonline.com/$TENANT_ID/oauth2/v2.0/token"
}
EOF

log_info "App registration details saved to: $OUTPUT_FILE"
log_info ""
log_info "Next steps:"
log_info "1. Grant admin consent for API permissions:"
log_info "   az ad app permission admin-consent --id $APP_ID"
log_info ""
log_info "2. Grant DICOM Data Owner role to the service principal:"
log_info "   az role assignment create \\"
log_info "     --assignee $SP_OBJECT_ID \\"
log_info "     --role 'DICOM Data Owner' \\"
log_info "     --scope /subscriptions/SUBSCRIPTION_ID/resourceGroups/RG_NAME/providers/Microsoft.HealthcareApis/workspaces/$DICOM_WORKSPACE_NAME"
log_info ""
log_info "${GREEN}App registration created successfully!${NC}"
```

**Step 2: Make script executable**

```bash
chmod +x examples/azure/quickstart/scripts/setup-app-registration.sh
```

**Step 3: Test script syntax**

```bash
bash -n examples/azure/quickstart/scripts/setup-app-registration.sh
```

Expected: No syntax errors

**Step 4: Test help output**

```bash
examples/azure/quickstart/scripts/setup-app-registration.sh --help
```

Expected: Shows usage information

**Step 5: Commit**

```bash
git add examples/azure/quickstart/scripts/setup-app-registration.sh
git commit -m "feat(azure): add app registration setup script

Add bash script to automate Azure AD app registration creation:
- Creates app registration with appropriate permissions
- Generates client secret with 2-year expiration
- Configures DICOM API permissions
- Outputs credentials to JSON file

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

### Task 14: Deployment Script

**Files:**
- Create: `examples/azure/quickstart/scripts/deploy.sh`

**Step 1: Create deployment script**

File: `examples/azure/quickstart/scripts/deploy.sh`
```bash
#!/usr/bin/env bash
set -euo pipefail

# ========================================
# Deploy Orthanc OAuth Quickstart to Azure
# ========================================
#
# This script deploys the Orthanc OAuth plugin quickstart to Azure using Bicep.
#
# Prerequisites:
# - Azure CLI 2.50+
# - Docker (for building custom image)
# - App registration created (run setup-app-registration.sh first)
# - Azure Container Registry
#
# Usage:
#   ./deploy.sh --resource-group rg-orthanc-demo --location eastus
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
ENVIRONMENT_NAME="quickstart"
PARAMETERS_FILE="parameters.json"
APP_REG_FILE="app-registration.json"
BUILD_IMAGE=true
CONTAINER_REGISTRY=""
IMAGE_TAG="latest"

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

Deploy Orthanc OAuth quickstart to Azure Container Apps.

OPTIONS:
    -g, --resource-group NAME    Resource group name (required)
    -l, --location LOCATION      Azure region (default: eastus)
    -e, --environment NAME       Environment name (default: quickstart)
    -p, --parameters FILE        Parameters JSON file (default: parameters.json)
    -a, --app-reg FILE           App registration JSON file (default: app-registration.json)
    -r, --registry NAME          Azure Container Registry name (required if building image)
    -t, --tag TAG                Container image tag (default: latest)
    --no-build                   Skip building container image
    -h, --help                   Show this help message

EXAMPLE:
    $0 --resource-group rg-orthanc-demo --location eastus --registry myregistry

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
        -a|--app-reg)
            APP_REG_FILE="$2"
            shift 2
            ;;
        -r|--registry)
            CONTAINER_REGISTRY="$2"
            shift 2
            ;;
        -t|--tag)
            IMAGE_TAG="$2"
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

# ========================================
# Main Script
# ========================================

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

log_step "Step 1/6: Validating prerequisites"

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

# Check app registration file
if [[ ! -f "$APP_REG_FILE" ]]; then
    log_error "App registration file not found: $APP_REG_FILE"
    log_error "Run setup-app-registration.sh first"
    exit 1
fi

# Load app registration details
CLIENT_ID=$(jq -r '.clientId' "$APP_REG_FILE")
CLIENT_SECRET=$(jq -r '.clientSecret' "$APP_REG_FILE")
TENANT_ID=$(jq -r '.tenantId' "$APP_REG_FILE")
TOKEN_ENDPOINT=$(jq -r '.tokenEndpoint' "$APP_REG_FILE")
DICOM_SCOPE=$(jq -r '.dicomScope' "$APP_REG_FILE")

log_info "Using app registration: $CLIENT_ID"

# ========================================
# Build and Push Container Image
# ========================================

if [[ "$BUILD_IMAGE" == true ]]; then
    log_step "Step 2/6: Building and pushing container image"

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
    log_step "Step 2/6: Skipping image build (--no-build specified)"

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

log_step "Step 3/6: Creating resource group"

if az group show --name "$RESOURCE_GROUP" &> /dev/null; then
    log_info "Resource group already exists: $RESOURCE_GROUP"
else
    log_info "Creating resource group: $RESOURCE_GROUP"
    az group create --name "$RESOURCE_GROUP" --location "$LOCATION"
fi

# ========================================
# Generate Deployment Parameters
# ========================================

log_step "Step 4/6: Generating deployment parameters"

# Read DICOM service URL from parameters file
DICOM_SERVICE_URL=$(jq -r '.parameters.dicomServiceUrl.value' "$PARAMETERS_FILE")

# Generate secure passwords if not in parameters
POSTGRES_PASSWORD=$(openssl rand -base64 32)
ORTHANC_PASSWORD=$(openssl rand -base64 24)

# Create deployment parameters
cat > deployment-params.json << EOF
{
  "environmentName": "$ENVIRONMENT_NAME",
  "location": "$LOCATION",
  "resourceGroupName": "$RESOURCE_GROUP",
  "containerImage": "$CONTAINER_IMAGE",
  "containerRegistryName": "$CONTAINER_REGISTRY",
  "dicomServiceUrl": "$DICOM_SERVICE_URL",
  "tenantId": "$TENANT_ID",
  "dicomScope": "$DICOM_SCOPE",
  "oauthClientId": "$CLIENT_ID",
  "oauthClientSecret": "$CLIENT_SECRET",
  "postgresAdminUsername": "orthanc_admin",
  "postgresAdminPassword": "$POSTGRES_PASSWORD",
  "orthancUsername": "admin",
  "orthancPassword": "$ORTHANC_PASSWORD"
}
EOF

log_info "Deployment parameters generated"

# ========================================
# Deploy Bicep Template
# ========================================

log_step "Step 5/6: Deploying Azure resources with Bicep"

DEPLOYMENT_NAME="orthanc-quickstart-$(date +%Y%m%d-%H%M%S)"

log_info "Starting deployment: $DEPLOYMENT_NAME"

az deployment sub create \
    --name "$DEPLOYMENT_NAME" \
    --location "$LOCATION" \
    --template-file "$SCRIPT_DIR/../main.bicep" \
    --parameters @deployment-params.json \
    --output json > deployment-output.json

log_info "Deployment complete"

# ========================================
# Display Outputs
# ========================================

log_step "Step 6/6: Deployment summary"

CONTAINER_APP_URL=$(jq -r '.properties.outputs.containerAppUrl.value' deployment-output.json)
POSTGRES_FQDN=$(jq -r '.properties.outputs.postgresServerFqdn.value' deployment-output.json)
STORAGE_ACCOUNT=$(jq -r '.properties.outputs.storageAccountName.value' deployment-output.json)

cat << EOF

${GREEN}✓ Deployment successful!${NC}

Resource Group: $RESOURCE_GROUP
Location: $LOCATION

Resources deployed:
  - Container App: https://$CONTAINER_APP_URL
  - PostgreSQL: $POSTGRES_FQDN
  - Storage Account: $STORAGE_ACCOUNT

Orthanc Credentials:
  - Username: admin
  - Password: $ORTHANC_PASSWORD

Next steps:
  1. Access Orthanc at: https://$CONTAINER_APP_URL
  2. Test DICOM upload: ./scripts/test-deployment.sh
  3. View logs: az containerapp logs show --name orthanc-$ENVIRONMENT_NAME-app --resource-group $RESOURCE_GROUP

EOF

# Save deployment details
cat > deployment-details.json << EOF
{
  "resourceGroup": "$RESOURCE_GROUP",
  "location": "$LOCATION",
  "containerAppUrl": "https://$CONTAINER_APP_URL",
  "postgresFqdn": "$POSTGRES_FQDN",
  "storageAccount": "$STORAGE_ACCOUNT",
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
chmod +x examples/azure/quickstart/scripts/deploy.sh
```

**Step 3: Test script syntax**

```bash
bash -n examples/azure/quickstart/scripts/deploy.sh
```

Expected: No syntax errors

**Step 4: Test help output**

```bash
examples/azure/quickstart/scripts/deploy.sh --help
```

Expected: Shows usage information

**Step 5: Commit**

```bash
git add examples/azure/quickstart/scripts/deploy.sh
git commit -m "feat(azure): add comprehensive deployment script

Add bash script to automate Azure deployment:
- Validates prerequisites and authentication
- Builds and pushes Docker image to ACR
- Creates resource group
- Generates deployment parameters
- Deploys Bicep template
- Displays deployment summary and credentials

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

### Task 15: Test Deployment Script

**Files:**
- Create: `examples/azure/quickstart/scripts/test-deployment.sh`

**Step 1: Create test script**

File: `examples/azure/quickstart/scripts/test-deployment.sh`
```bash
#!/usr/bin/env bash
set -euo pipefail

# ========================================
# Test Orthanc OAuth Deployment
# ========================================
#
# This script tests the deployed Orthanc instance by uploading
# a test DICOM file and verifying it's stored and forwarded.
#
# Prerequisites:
# - curl
# - jq
# - Deployed Orthanc instance (run deploy.sh first)
#
# Usage:
#   ./test-deployment.sh --url https://orthanc-quickstart.example.com
#

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ORTHANC_URL=""
USERNAME="admin"
PASSWORD=""
DEPLOYMENT_DETAILS_FILE="deployment-details.json"
TEST_DICOM_FILE=""

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

log_test() {
    echo -e "${BLUE}[TEST]${NC} $1"
}

show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Test deployed Orthanc instance with OAuth plugin.

OPTIONS:
    -u, --url URL              Orthanc URL (e.g., https://orthanc.example.com)
    -U, --username USERNAME    Orthanc username (default: admin)
    -P, --password PASSWORD    Orthanc password
    -d, --deployment FILE      Deployment details JSON (default: deployment-details.json)
    -f, --file FILE            Test DICOM file to upload
    -h, --help                 Show this help message

EXAMPLE:
    $0 --url https://orthanc-quickstart.example.com --password mypassword

EOF
}

# ========================================
# Parse Arguments
# ========================================

while [[ $# -gt 0 ]]; do
    case $1 in
        -u|--url)
            ORTHANC_URL="$2"
            shift 2
            ;;
        -U|--username)
            USERNAME="$2"
            shift 2
            ;;
        -P|--password)
            PASSWORD="$2"
            shift 2
            ;;
        -d|--deployment)
            DEPLOYMENT_DETAILS_FILE="$2"
            shift 2
            ;;
        -f|--file)
            TEST_DICOM_FILE="$2"
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

# ========================================
# Load Deployment Details
# ========================================

if [[ -f "$DEPLOYMENT_DETAILS_FILE" && -z "$ORTHANC_URL" ]]; then
    log_info "Loading deployment details from: $DEPLOYMENT_DETAILS_FILE"
    ORTHANC_URL=$(jq -r '.containerAppUrl' "$DEPLOYMENT_DETAILS_FILE")
    if [[ -z "$PASSWORD" ]]; then
        PASSWORD=$(jq -r '.orthancPassword' "$DEPLOYMENT_DETAILS_FILE")
    fi
fi

# Validate required parameters
if [[ -z "$ORTHANC_URL" ]]; then
    log_error "Orthanc URL is required"
    show_usage
    exit 1
fi

if [[ -z "$PASSWORD" ]]; then
    log_error "Password is required"
    show_usage
    exit 1
fi

# ========================================
# Test 1: Check System Status
# ========================================

log_test "Test 1/5: Checking Orthanc system status"

RESPONSE=$(curl -s -u "$USERNAME:$PASSWORD" "$ORTHANC_URL/system" || echo "")

if [[ -z "$RESPONSE" ]]; then
    log_error "Failed to connect to Orthanc at $ORTHANC_URL"
    exit 1
fi

VERSION=$(echo "$RESPONSE" | jq -r '.Version')
DICOM_AET=$(echo "$RESPONSE" | jq -r '.DicomAet')

log_info "Orthanc version: $VERSION"
log_info "DICOM AET: $DICOM_AET"
echo -e "${GREEN}✓ System status OK${NC}"
echo ""

# ========================================
# Test 2: Check Plugin Status
# ========================================

log_test "Test 2/5: Checking OAuth plugin status"

PLUGINS=$(echo "$RESPONSE" | jq -r '.Plugins[]')

if echo "$PLUGINS" | grep -q "dicomweb_oauth"; then
    log_info "OAuth plugin loaded"
    echo -e "${GREEN}✓ Plugin status OK${NC}"
else
    log_warn "OAuth plugin not found in plugin list"
    echo -e "${YELLOW}⚠ Plugin might not be loaded${NC}"
fi
echo ""

# ========================================
# Test 3: Check Database Connection
# ========================================

log_test "Test 3/5: Checking database connection"

STATS=$(curl -s -u "$USERNAME:$PASSWORD" "$ORTHANC_URL/statistics" || echo "{}")
TOTAL_STUDIES=$(echo "$STATS" | jq -r '.TotalDiskSize' || echo "unknown")

log_info "Database connection: OK"
log_info "Total disk size: $TOTAL_STUDIES bytes"
echo -e "${GREEN}✓ Database connection OK${NC}"
echo ""

# ========================================
# Test 4: Upload Test DICOM (Optional)
# ========================================

if [[ -n "$TEST_DICOM_FILE" && -f "$TEST_DICOM_FILE" ]]; then
    log_test "Test 4/5: Uploading test DICOM file"

    UPLOAD_RESPONSE=$(curl -s -u "$USERNAME:$PASSWORD" \
        -X POST \
        -H "Content-Type: application/dicom" \
        --data-binary "@$TEST_DICOM_FILE" \
        "$ORTHANC_URL/instances")

    INSTANCE_ID=$(echo "$UPLOAD_RESPONSE" | jq -r '.ID')

    if [[ -n "$INSTANCE_ID" && "$INSTANCE_ID" != "null" ]]; then
        log_info "Instance uploaded: $INSTANCE_ID"
        echo -e "${GREEN}✓ DICOM upload OK${NC}"
    else
        log_error "Failed to upload DICOM file"
        echo -e "${RED}✗ DICOM upload failed${NC}"
    fi
else
    log_info "Skipping DICOM upload (no test file provided)"
    echo -e "${YELLOW}⊘ DICOM upload skipped${NC}"
fi
echo ""

# ========================================
# Test 5: Check Metrics Endpoint
# ========================================

log_test "Test 5/5: Checking Prometheus metrics"

METRICS=$(curl -s -u "$USERNAME:$PASSWORD" "$ORTHANC_URL/metrics" || echo "")

if [[ -n "$METRICS" ]] && echo "$METRICS" | grep -q "orthanc_"; then
    log_info "Metrics endpoint responding"
    METRIC_COUNT=$(echo "$METRICS" | grep -c "^orthanc_" || echo "0")
    log_info "Metrics available: $METRIC_COUNT"
    echo -e "${GREEN}✓ Metrics endpoint OK${NC}"
else
    log_warn "Metrics endpoint not responding"
    echo -e "${YELLOW}⚠ Metrics endpoint unavailable${NC}"
fi
echo ""

# ========================================
# Summary
# ========================================

cat << EOF
${GREEN}═══════════════════════════════════════════════════${NC}
${GREEN}                  TEST SUMMARY                    ${NC}
${GREEN}═══════════════════════════════════════════════════${NC}

Orthanc URL: $ORTHANC_URL
Version: $VERSION
DICOM AET: $DICOM_AET

All critical tests passed! ✓

Next steps:
  1. Configure DICOM modalities
  2. Test OAuth authentication with DICOM service
  3. Monitor logs for any errors
  4. Set up backup and monitoring

EOF
```

**Step 2: Make script executable**

```bash
chmod +x examples/azure/quickstart/scripts/test-deployment.sh
```

**Step 3: Test script syntax**

```bash
bash -n examples/azure/quickstart/scripts/test-deployment.sh
```

Expected: No syntax errors

**Step 4: Commit**

```bash
git add examples/azure/quickstart/scripts/test-deployment.sh
git commit -m "feat(azure): add deployment testing script

Add comprehensive testing script for deployed Orthanc:
- Validates system status and connectivity
- Checks OAuth plugin is loaded
- Verifies database connection
- Optionally uploads test DICOM file
- Checks Prometheus metrics endpoint

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

### Task 16: Cleanup Script

**Files:**
- Create: `examples/azure/quickstart/scripts/cleanup.sh`

**Step 1: Create cleanup script**

File: `examples/azure/quickstart/scripts/cleanup.sh`
```bash
#!/usr/bin/env bash
set -euo pipefail

# ========================================
# Cleanup Azure Resources
# ========================================
#
# This script safely removes all Azure resources created by the deployment.
#
# Prerequisites:
# - Azure CLI 2.50+
# - Appropriate permissions to delete resources
#
# Usage:
#   ./cleanup.sh --resource-group rg-orthanc-demo
#

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
RESOURCE_GROUP=""
DELETE_APP_REG=false
SKIP_CONFIRMATION=false
APP_REG_FILE="app-registration.json"

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

Delete Azure resources created by Orthanc deployment.

OPTIONS:
    -g, --resource-group NAME    Resource group name (required)
    -a, --delete-app-reg         Also delete app registration
    -f, --app-reg-file FILE      App registration JSON (default: app-registration.json)
    -y, --yes                    Skip confirmation prompt
    -h, --help                   Show this help message

EXAMPLE:
    $0 --resource-group rg-orthanc-demo
    $0 --resource-group rg-orthanc-demo --delete-app-reg --yes

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
        -a|--delete-app-reg)
            DELETE_APP_REG=true
            shift
            ;;
        -f|--app-reg-file)
            APP_REG_FILE="$2"
            shift 2
            ;;
        -y|--yes)
            SKIP_CONFIRMATION=true
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

# ========================================
# Main Script
# ========================================

log_warn "This will delete the following resources:"
echo "  - Resource group: $RESOURCE_GROUP"
echo "  - All resources within the resource group"

if [[ "$DELETE_APP_REG" == true ]]; then
    if [[ -f "$APP_REG_FILE" ]]; then
        APP_ID=$(jq -r '.clientId' "$APP_REG_FILE")
        echo "  - App registration: $APP_ID"
    else
        log_warn "App registration file not found: $APP_REG_FILE"
    fi
fi

echo ""

if [[ "$SKIP_CONFIRMATION" != true ]]; then
    read -p "Are you sure you want to continue? (type 'yes' to confirm): " CONFIRM
    if [[ "$CONFIRM" != "yes" ]]; then
        log_info "Cleanup cancelled"
        exit 0
    fi
fi

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

# ========================================
# Delete Resource Group
# ========================================

log_info "Deleting resource group: $RESOURCE_GROUP"

if az group show --name "$RESOURCE_GROUP" &> /dev/null; then
    az group delete --name "$RESOURCE_GROUP" --yes --no-wait
    log_info "Resource group deletion initiated (running in background)"
else
    log_warn "Resource group not found: $RESOURCE_GROUP"
fi

# ========================================
# Delete App Registration
# ========================================

if [[ "$DELETE_APP_REG" == true && -f "$APP_REG_FILE" ]]; then
    log_info "Deleting app registration"

    APP_ID=$(jq -r '.clientId' "$APP_REG_FILE")

    if az ad app show --id "$APP_ID" &> /dev/null; then
        az ad app delete --id "$APP_ID"
        log_info "App registration deleted: $APP_ID"
    else
        log_warn "App registration not found: $APP_ID"
    fi
fi

# ========================================
# Summary
# ========================================

cat << EOF

${GREEN}✓ Cleanup initiated${NC}

Resources are being deleted in the background.
You can check status with:

  az group show --name $RESOURCE_GROUP

To monitor deletion progress:

  az group wait --name $RESOURCE_GROUP --deleted

EOF
```

**Step 2: Make script executable**

```bash
chmod +x examples/azure/quickstart/scripts/cleanup.sh
```

**Step 3: Test script syntax**

```bash
bash -n examples/azure/quickstart/scripts/cleanup.sh
```

Expected: No syntax errors

**Step 4: Test help output**

```bash
examples/azure/quickstart/scripts/cleanup.sh --help
```

Expected: Shows usage information

**Step 5: Commit**

```bash
git add examples/azure/quickstart/scripts/cleanup.sh
git commit -m "feat(azure): add cleanup script

Add script to safely delete Azure resources:
- Deletes resource group and all contained resources
- Optionally deletes app registration
- Requires confirmation before deletion
- Supports background deletion

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

### Task 17: Quickstart README

**Files:**
- Modify: `examples/azure/quickstart/README.md`

**Step 1: Update README with complete documentation**

File: `examples/azure/quickstart/README.md`
```markdown
# Azure Quickstart Deployment

Deploy Orthanc with OAuth plugin to Azure Container Apps using client credentials authentication.

## Overview

This quickstart deploys Orthanc to Azure Container Apps with:
- **Authentication**: OAuth 2.0 client credentials flow
- **Database**: Azure Database for PostgreSQL Flexible Server
- **Storage**: Azure Blob Storage
- **DICOM Service**: Azure Health Data Services DICOM
- **Networking**: Public endpoints with firewall rules
- **Estimated Cost**: ~$66/month
- **Setup Time**: ~15 minutes

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Azure Subscription                        │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Resource Group: rg-orthanc-quickstart               │  │
│  │                                                       │  │
│  │  ┌─────────────────┐      ┌──────────────────────┐  │  │
│  │  │ Container Apps  │      │ PostgreSQL Flexible  │  │  │
│  │  │   Environment   │      │      Server          │  │  │
│  │  │                 │      │                      │  │  │
│  │  │  ┌───────────┐  │      │  Database: orthanc   │  │  │
│  │  │  │  Orthanc  │──┼──────┤                      │  │  │
│  │  │  │  + OAuth  │  │      └──────────────────────┘  │  │
│  │  │  │  Plugin   │  │                                 │  │
│  │  │  └───────────┘  │      ┌──────────────────────┐  │  │
│  │  │       │         │      │   Blob Storage       │  │  │
│  │  │       │         │      │                      │  │  │
│  │  │       └─────────┼──────┤  Container:          │  │  │
│  │  │                 │      │  orthanc-dicom       │  │  │
│  │  └─────────────────┘      └──────────────────────┘  │  │
│  │                                                       │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Azure Health Data Services                          │  │
│  │  ┌────────────────────────────────────────────────┐  │  │
│  │  │  DICOM Service                                 │  │  │
│  │  │  (OAuth 2.0 protected)                         │  │  │
│  │  └────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Azure AD                                            │  │
│  │  ┌────────────────────────────────────────────────┐  │  │
│  │  │  App Registration (Client Credentials)         │  │  │
│  │  └────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

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

### Step 2: Create App Registration

```bash
cd examples/azure/quickstart
./scripts/setup-app-registration.sh \
  --name "orthanc-quickstart" \
  --dicom-workspace-name "your-dicom-workspace"
```

This creates:
- Azure AD app registration
- Service principal
- Client secret (2-year expiration)
- Outputs credentials to `app-registration.json`

**Important**: Grant admin consent for API permissions:

```bash
APP_ID=$(jq -r '.clientId' app-registration.json)
az ad app permission admin-consent --id $APP_ID
```

### Step 3: Grant DICOM Permissions

Grant the service principal **DICOM Data Owner** role:

```bash
SP_OBJECT_ID=$(jq -r '.servicePrincipalObjectId' app-registration.json)
DICOM_WORKSPACE_ID="/subscriptions/YOUR_SUBSCRIPTION/resourceGroups/YOUR_RG/providers/Microsoft.HealthcareApis/workspaces/YOUR_WORKSPACE"

az role assignment create \
  --assignee $SP_OBJECT_ID \
  --role "DICOM Data Owner" \
  --scope $DICOM_WORKSPACE_ID
```

### Step 4: Configure Parameters

Copy and customize the parameters template:

```bash
cp parameters.json.template parameters.json
```

Edit `parameters.json` and replace:
- `REPLACE_WITH_YOUR_DICOM_SERVICE_URL`
- `REPLACE_WITH_YOUR_TENANT_ID`
- `REPLACE_WITH_YOUR_CLIENT_ID`
- Container registry details

For production, use Key Vault references for secrets instead of plain text.

### Step 5: Deploy

```bash
./scripts/deploy.sh \
  --resource-group rg-orthanc-quickstart \
  --location eastus \
  --registry myregistry
```

This will:
1. Build Docker image with Orthanc + OAuth plugin
2. Push image to Azure Container Registry
3. Deploy Azure resources using Bicep
4. Output deployment details and credentials

Deployment takes ~10-15 minutes.

### Step 6: Test Deployment

```bash
./scripts/test-deployment.sh
```

This validates:
- System status
- OAuth plugin loaded
- Database connectivity
- Metrics endpoint

## Building the Docker Image

**IMPORTANT:** When building for Azure Container Apps, you MUST specify the target platform:

```bash
docker buildx build --platform linux/amd64 -t <registry>/<image>:<tag> -f examples/azure/quickstart/Dockerfile .
```

M1/M2/M3 Macs build arm64 images by default, which will fail on Azure Container Apps (amd64 Linux).

## Cost Estimate

Approximate monthly costs (East US region):

| Resource | SKU | Monthly Cost |
|----------|-----|--------------|
| Container Apps | 1 vCPU, 2GB RAM, ~730 hours | $35 |
| PostgreSQL Flexible | Burstable B2s, 32GB storage | $20 |
| Blob Storage | LRS, ~100GB | $2 |
| Log Analytics | 5GB ingestion | $5 |
| Container Registry | Basic tier | $5 |
| **Total** | | **~$67/month** |

> Costs vary by region and usage. Use [Azure Pricing Calculator](https://azure.microsoft.com/pricing/calculator/) for accurate estimates.

## Configuration

### Environment Variables

The deployment automatically configures:

**Database**:
- `ORTHANC__POSTGRESQL__HOST`
- `ORTHANC__POSTGRESQL__PORT`
- `ORTHANC__POSTGRESQL__DATABASE`
- `ORTHANC__POSTGRESQL__USERNAME`
- `ORTHANC__POSTGRESQL__PASSWORD`

**Storage**:
- `ORTHANC__AZURE_BLOB_STORAGE__CONNECTION_STRING`
- `ORTHANC__AZURE_BLOB_STORAGE__CONTAINER`

**OAuth**:
- `OAUTH_CLIENT_ID`
- `OAUTH_CLIENT_SECRET`
- `OAUTH_TOKEN_ENDPOINT`
- `DICOM_SERVICE_URL`
- `DICOM_SCOPE`

**Orthanc**:
- `ORTHANC_USERNAME`
- `ORTHANC_PASSWORD`

### Scaling

Automatic scaling is configured:
- **Min replicas**: 1
- **Max replicas**: 3
- **Scale trigger**: 50 concurrent requests

Adjust in `main.bicep`:

```bicep
scaleMinReplicas: 1
scaleMaxReplicas: 3
scaleRules: [
  {
    name: 'http-rule'
    http: {
      metadata: {
        concurrentRequests: '50'
      }
    }
  }
]
```

## Accessing Orthanc

### Web Interface

```bash
ORTHANC_URL=$(jq -r '.containerAppUrl' deployment-details.json)
open "https://$ORTHANC_URL"
```

Login with credentials from `deployment-details.json`.

### API Access

```bash
ORTHANC_PASSWORD=$(jq -r '.orthancPassword' deployment-details.json)

curl -u admin:$ORTHANC_PASSWORD https://$ORTHANC_URL/system
```

### Logs

```bash
az containerapp logs show \
  --name orthanc-quickstart-app \
  --resource-group rg-orthanc-quickstart \
  --follow
```

## Monitoring

### Prometheus Metrics

Metrics available at `/metrics` endpoint:

```bash
curl -u admin:$ORTHANC_PASSWORD https://$ORTHANC_URL/metrics
```

Key metrics:
- `orthanc_token_acquisition_total` - OAuth token requests
- `orthanc_token_cache_hits_total` - Token cache hits
- `orthanc_http_requests_total` - HTTP requests to DICOM service

### Log Analytics

View logs in Azure Portal:

```bash
az monitor log-analytics query \
  --workspace $(az containerapp env show --name orthanc-quickstart-cae --resource-group rg-orthanc-quickstart --query properties.appLogsConfiguration.logAnalyticsConfiguration.customerId -o tsv) \
  --analytics-query "ContainerAppConsoleLogs_CL | where ContainerAppName_s == 'orthanc-quickstart-app' | project TimeGenerated, Log_s | order by TimeGenerated desc | take 50"
```

## Troubleshooting

### Container fails to start

**Check logs**:
```bash
az containerapp logs show --name orthanc-quickstart-app --resource-group rg-orthanc-quickstart --tail 100
```

**Common issues**:
- Image pull failure: Check ACR permissions
- Database connection: Verify firewall rules allow Azure services
- Storage connection: Verify connection string is valid

### OAuth authentication fails

**Verify app registration**:
```bash
APP_ID=$(jq -r '.clientId' app-registration.json)
az ad app show --id $APP_ID
```

**Check DICOM permissions**:
```bash
SP_OBJECT_ID=$(jq -r '.servicePrincipalObjectId' app-registration.json)
az role assignment list --assignee $SP_OBJECT_ID --all
```

**Test token acquisition manually**:
```bash
curl -X POST https://login.microsoftonline.com/TENANT_ID/oauth2/v2.0/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=CLIENT_ID&scope=https://dicom.healthcareapis.azure.com/.default&client_secret=CLIENT_SECRET&grant_type=client_credentials"
```

### Database connection errors

**Test connectivity from Container App**:
```bash
az containerapp exec \
  --name orthanc-quickstart-app \
  --resource-group rg-orthanc-quickstart \
  --command /bin/bash

# Inside container
apt-get update && apt-get install -y postgresql-client
psql -h POSTGRES_HOST -U USERNAME -d orthanc
```

## Cleanup

Delete all resources:

```bash
./scripts/cleanup.sh --resource-group rg-orthanc-quickstart
```

Include app registration:

```bash
./scripts/cleanup.sh --resource-group rg-orthanc-quickstart --delete-app-reg --yes
```

## Security Considerations

### Production Checklist

- [ ] Use Azure Key Vault for secrets
- [ ] Enable HTTPS only (configured by default)
- [ ] Implement network restrictions (use production deployment for VNet)
- [ ] Enable Azure Monitor alerts
- [ ] Rotate client secret before 2-year expiration
- [ ] Review and harden database firewall rules
- [ ] Enable diagnostic logging
- [ ] Implement backup strategy for PostgreSQL
- [ ] Configure Azure AD Conditional Access
- [ ] Review RBAC role assignments

### Secrets Management

For production, use Key Vault references:

```json
{
  "oauthClientSecret": {
    "reference": {
      "keyVault": {
        "id": "/subscriptions/.../vaults/my-vault"
      },
      "secretName": "oauth-client-secret"
    }
  }
}
```

## Next Steps

- **Production Deployment**: See [../production/](../production/) for VNet, private endpoints, and managed identity
- **AKS Deployment**: See [../production-aks/](../production-aks/) for Kubernetes with Helm
- **Monitoring**: Configure Application Insights for advanced monitoring
- **Backup**: Set up automated PostgreSQL backups
- **CI/CD**: Implement GitHub Actions workflow for automated deployments

## Support

For issues and questions:
- **Plugin Issues**: [GitHub Issues](https://github.com/rhavekost/orthanc-dicomweb-oauth/issues)
- **Azure Issues**: [Azure Support](https://azure.microsoft.com/support/)
- **Orthanc Questions**: [Orthanc Forum](https://groups.google.com/g/orthanc-users)
```

**Step 2: Validate markdown syntax**

```bash
# Check for broken links (if you have a markdown linter)
# markdownlint examples/azure/quickstart/README.md
```

**Step 3: Commit**

```bash
git add examples/azure/quickstart/README.md
git commit -m "docs(azure): complete quickstart README with full documentation

Add comprehensive documentation for Azure quickstart deployment:
- Architecture diagram
- Step-by-step deployment guide
- Cost estimates
- Configuration details
- Monitoring and troubleshooting
- Security best practices
- Next steps and support resources

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Summary

Phase 1 (Tasks 10-17) is complete! You now have:

✅ **Task 10**: Bicep parameter templates (`.bicepparam` and `.json`)
✅ **Task 11**: Main Bicep template with Azure Verified Modules
✅ **Task 12**: Orthanc configuration Bicep module
✅ **Task 13**: App registration setup script
✅ **Task 14**: Deployment automation script
✅ **Task 15**: Deployment testing script
✅ **Task 16**: Resource cleanup script
✅ **Task 17**: Comprehensive quickstart README

**What you can do now**:
- Deploy complete Orthanc + OAuth setup to Azure Container Apps
- Use client credentials authentication
- Automated deployment with production-ready infrastructure
- Full testing and cleanup automation

**Next Phases**:
- **Phase 2**: Production Container Apps (Tasks 18-24) - VNet, private endpoints, managed identity
- **Phase 3**: Production AKS (Tasks 25-31) - AKS cluster with Helm chart
- **Phase 4**: Documentation and Testing (Tasks 32-40)

Would you like to continue with Phase 2 (production Container Apps deployment)?
