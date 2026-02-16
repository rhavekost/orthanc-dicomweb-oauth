targetScope = 'subscription'

// ========================================
// Infrastructure-Only Deployment
// Deploys: VNet, ACR, PostgreSQL, Storage, Healthcare APIs
// Does NOT deploy: Container App (deployed separately after image build)
// ========================================

// ========================================
// Parameters
// ========================================

@description('The name of the environment')
param environmentName string

@description('The Azure region')
param location string

@description('The name of the resource group')
param resourceGroupName string

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
}

// ========================================
// Container Registry (No Private Endpoint for Standard SKU)
// ========================================

module containerRegistry './modules/container-registry-simple.bicep' = {
  scope: rg
  name: 'containerRegistryDeployment'
  params: {
    registryName: containerRegistryName
    location: location
    adminUserEnabled: true
    tags: tags
  }
}

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
}

module postgresConfig '../quickstart/modules/postgres-config.bicep' = {
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

module healthcareWorkspace '../quickstart/modules/healthcare-workspace.bicep' = {
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
// Outputs
// ========================================

output resourceGroupName string = rg.name
output containerRegistryName string = containerRegistry.outputs.registryName
output containerRegistryLoginServer string = containerRegistry.outputs.loginServer
output containerRegistryAdminUsername string = containerRegistry.outputs.adminUsername
output containerRegistryAdminPassword string = containerRegistry.outputs.adminPassword
output dicomServiceUrl string = healthcareWorkspace.outputs.dicomServiceUrl
output dicomServiceId string = healthcareWorkspace.outputs.dicomServiceId
output postgresServerFqdn string = '${postgresServerName}.postgres.database.azure.com'
output postgresServerName string = postgresServerName
output storageAccountName string = storage.outputs.storageAccountName
output storageAccountId string = storage.outputs.storageAccountId
output storageContainerName string = storage.outputs.containerName
#disable-next-line outputs-should-not-contain-secrets
output storageConnectionString string = storage.outputs.storageConnectionString
output vnetId string = network.outputs.vnetId
output containerAppsSubnetId string = network.outputs.containerAppsSubnetId
