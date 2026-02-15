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

@description('The SKU for the registry (Standard or Premium required for private endpoints)')
param sku string = 'Standard'

@description('Disable admin user')
param adminUserEnabled bool = false

@description('Public network access (Disabled requires Premium SKU, Standard requires Enabled)')
param publicNetworkAccess string = 'Enabled'

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

module acrPrivateEndpoint './private-endpoint.bicep' = {
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
