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
// Container Registry with Private Endpoint
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
    containerRegistryServer: containerRegistry.outputs.loginServer
    containerRegistryUsername: containerRegistry.outputs.adminUsername
    containerRegistryPassword: containerRegistry.outputs.adminPassword
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
    containerRegistry
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
