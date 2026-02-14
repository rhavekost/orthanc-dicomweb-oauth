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
    infrastructureSubnetId: networking.outputs.containerAppsSubnetId
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
