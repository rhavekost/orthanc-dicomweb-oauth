// ========================================
// Container Registry Module (No Private Endpoint)
// Standard SKU does not support private endpoints
// Use Premium SKU or remove private endpoint
// ========================================

@description('The name of the container registry')
param registryName string

@description('The location for the registry')
param location string

@description('The SKU for the registry')
param sku string = 'Standard'

@description('Enable admin user for deployment')
param adminUserEnabled bool = true

@description('Public network access (Standard SKU requires Enabled)')
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
// Outputs
// ========================================

output registryId string = containerRegistry.id
output registryName string = containerRegistry.name
output loginServer string = containerRegistry.properties.loginServer
