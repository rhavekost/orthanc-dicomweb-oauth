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

module blobPrivateEndpoint './private-endpoint.bicep' = {
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
