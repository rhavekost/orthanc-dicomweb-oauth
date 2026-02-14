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

@description('Azure Container Registry admin password')
@secure()
param containerRegistryPassword string

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
// Log Analytics Workspace (AVM)
// ========================================

module logAnalytics 'br/public:avm/res/operational-insights/workspace:0.9.1' = {
  scope: rg
  name: 'logAnalyticsDeployment'
  params: {
    name: logAnalyticsName
    location: location
    tags: tags
    dataRetention: 30
    skuName: 'PerGB2018'
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

// Reference to deployed storage account for getting keys (scoped to resource group)
resource storageAccountResource 'Microsoft.Storage/storageAccounts@2023-05-01' existing = {
  name: storageAccountName
  scope: rg
  dependsOn: [
    storageAccount
  ]
}

// ========================================
// PostgreSQL Flexible Server (AVM)
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
    zoneRedundant: false
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
            value: '${environment().authentication.loginEndpoint}${tenantId}/oauth2/v2.0/token'
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
          value: 'DefaultEndpointsProtocol=https;AccountName=${storageAccountResource.name};AccountKey=${storageAccountResource.listKeys().keys[0].value};EndpointSuffix=${environment().suffixes.storage}'
        }
        {
          name: 'oauth-client-secret'
          value: oauthClientSecret
        }
        {
          name: 'orthanc-password'
          value: orthancPassword
        }
        {
          name: 'acr-password'
          value: containerRegistryPassword
        }
      ]
    }
    ingressExternal: true
    ingressTargetPort: 8042
    ingressTransport: 'http'
    ingressAllowInsecure: false
    trafficLatestRevision: true
    trafficWeight: 100
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
        username: containerRegistryName
        passwordSecretRef: 'acr-password'
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

// NOTE: ACR Pull role assignment not needed when using admin credentials
// Container App uses username/password authentication for ACR

// ========================================
// Outputs
// ========================================

output resourceGroupName string = rg.name
output containerAppUrl string = containerApp.outputs.fqdn
output postgresServerFqdn string = postgres.outputs.fqdn
output storageAccountName string = storageAccount.outputs.name
output containerAppIdentityPrincipalId string = containerApp.outputs.systemAssignedMIPrincipalId
