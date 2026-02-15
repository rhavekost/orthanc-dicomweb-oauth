// ============================================================================
// Azure Container Registry Module
// ============================================================================
// Creates a container registry for storing the Orthanc OAuth Docker image

@description('The name of the container registry (must be globally unique, alphanumeric only)')
param registryName string

@description('The Azure region where the registry will be deployed')
param location string

@description('Resource tags')
param tags object = {}

@description('The SKU of the container registry')
@allowed([
  'Basic'
  'Standard'
  'Premium'
])
param sku string = 'Basic'

@description('Enable admin user for username/password authentication')
param adminUserEnabled bool = true

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
    publicNetworkAccess: 'Enabled'
    networkRuleBypassOptions: 'AzureServices'
    policies: {
      retentionPolicy: {
        days: 7
        status: 'disabled'
      }
      quarantinePolicy: {
        status: 'disabled'
      }
    }
  }
}

// ========================================
// Outputs
// ========================================

@description('The resource ID of the container registry')
output resourceId string = containerRegistry.id

@description('The name of the container registry')
output name string = containerRegistry.name

@description('The login server URL')
output loginServer string = containerRegistry.properties.loginServer

@description('The admin username (if admin user is enabled)')
output adminUsername string = adminUserEnabled ? containerRegistry.name : ''
