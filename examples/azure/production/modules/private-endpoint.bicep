// ========================================
// Private Endpoint Module (Reusable)
// ========================================
// Creates a private endpoint for any Azure service

@description('The name of the private endpoint')
param privateEndpointName string

@description('The location for the private endpoint')
param location string

@description('The ID of the subnet for the private endpoint')
param subnetId string

@description('The ID of the resource to create private endpoint for')
param privateLinkServiceId string

@description('The group IDs for the private endpoint (e.g., blob, registry)')
param groupIds array

@description('The ID of the Private DNS zone for automatic registration')
param privateDnsZoneId string

@description('Resource tags')
param tags object = {}

// ========================================
// Private Endpoint
// ========================================

resource privateEndpoint 'Microsoft.Network/privateEndpoints@2023-05-01' = {
  name: privateEndpointName
  location: location
  tags: tags
  properties: {
    subnet: {
      id: subnetId
    }
    privateLinkServiceConnections: [
      {
        name: privateEndpointName
        properties: {
          privateLinkServiceId: privateLinkServiceId
          groupIds: groupIds
        }
      }
    ]
  }
}

// ========================================
// Private DNS Zone Group
// ========================================

resource privateDnsZoneGroup 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2023-05-01' = {
  parent: privateEndpoint
  name: 'default'
  properties: {
    privateDnsZoneConfigs: [
      {
        name: 'config1'
        properties: {
          privateDnsZoneId: privateDnsZoneId
        }
      }
    ]
  }
}

// ========================================
// Outputs
// ========================================

output privateEndpointId string = privateEndpoint.id
output privateEndpointName string = privateEndpoint.name
