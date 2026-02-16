targetScope = 'resourceGroup'

// ========================================
// Container App Deployment
// Deploys: Container App + RBAC Assignments
// Requires: Infrastructure already deployed via main-infra.bicep
// ========================================

// ========================================
// Parameters
// ========================================

@description('The name of the environment')
param environmentName string

@description('The Azure region')
param location string

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

@description('Container Registry login server')
param containerRegistryLoginServer string

@description('Container Registry admin username')
param containerRegistryAdminUsername string

@description('Container Registry admin password')
@secure()
param containerRegistryAdminPassword string

@description('Container Registry resource ID')
param containerRegistryId string

@description('Container Apps subnet ID')
param containerAppsSubnetId string

@description('Storage connection string')
@secure()
param storageConnectionString string

@description('Storage container name')
param storageContainerName string

@description('Storage account resource ID')
param storageAccountId string

@description('DICOM service URL')
param dicomServiceUrl string

@description('DICOM service resource ID')
param dicomServiceId string

@description('PostgreSQL server name')
param postgresServerName string

@description('Resource tags')
param tags object = {}

// ========================================
// Variables
// ========================================

var resourcePrefix = 'orthanc-${environmentName}'
var containerAppName = '${resourcePrefix}-app'
var environmentNameContainerApps = '${resourcePrefix}-cae'
var containerImage = '${containerRegistryLoginServer}/orthanc-oauth:latest'
var postgresHost = '${postgresServerName}.postgres.database.azure.com'

// ========================================
// Container App with Managed Identity
// ========================================

module containerApp './modules/container-app.bicep' = {
  name: 'containerAppDeployment'
  params: {
    containerAppName: containerAppName
    environmentName: environmentNameContainerApps
    location: location
    containerImage: containerImage
    containerRegistryServer: containerRegistryLoginServer
    containerRegistryUsername: containerRegistryAdminUsername
    containerRegistryPassword: containerRegistryAdminPassword
    containerAppsSubnetId: containerAppsSubnetId
    orthancUsername: orthancUsername
    orthancPassword: orthancPassword
    postgresHost: postgresHost
    postgresUsername: postgresAdminUsername
    postgresPassword: postgresAdminPassword
    storageConnectionString: storageConnectionString
    storageContainerName: storageContainerName
    dicomServiceUrl: dicomServiceUrl
    tags: tags
  }
}

// ========================================
// RBAC Assignments
// ========================================

module rbacAssignments './modules/rbac-assignments.bicep' = {
  name: 'rbacAssignmentsDeployment'
  params: {
    containerAppPrincipalId: containerApp.outputs.containerAppPrincipalId
    dicomServiceId: dicomServiceId
    storageAccountId: storageAccountId
    containerRegistryId: containerRegistryId
  }
}

// ========================================
// Outputs
// ========================================

output containerAppUrl string = containerApp.outputs.containerAppUrl
output containerAppId string = containerApp.outputs.containerAppId
output containerAppName string = containerApp.outputs.containerAppName
output containerAppPrincipalId string = containerApp.outputs.containerAppPrincipalId
