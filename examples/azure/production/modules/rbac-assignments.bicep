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
// Existing Resource References
// ========================================

resource dicomService 'Microsoft.HealthcareApis/workspaces/dicomservices@2024-03-31' existing = {
  name: '${split(dicomServiceId, '/')[8]}/${split(dicomServiceId, '/')[10]}'
}

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' existing = {
  name: split(storageAccountId, '/')[8]
}

resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-11-01-preview' existing = {
  name: split(containerRegistryId, '/')[8]
}

// ========================================
// DICOM Data Owner Assignment
// ========================================

resource dicomRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(dicomServiceId, containerAppPrincipalId, dicomDataOwnerRoleId)
  scope: dicomService
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
  name: guid(storageAccountId, containerAppPrincipalId, storageBlobDataContributorRoleId)
  scope: storageAccount
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
  name: guid(containerRegistryId, containerAppPrincipalId, acrPullRoleId)
  scope: containerRegistry
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
