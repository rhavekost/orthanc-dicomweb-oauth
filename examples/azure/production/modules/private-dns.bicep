// ========================================
// Private DNS Zones Module
// ========================================

@description('Virtual Network ID to link DNS zones to')
param vnetId string

@description('Virtual Network name for link naming')
param vnetName string

@description('Resource tags')
param tags object = {}

// ========================================
// Private DNS Zones
// ========================================

// Private DNS Zone for PostgreSQL
resource postgresDnsZone 'Microsoft.Network/privateDnsZones@2020-06-01' = {
  name: 'privatelink.postgres.database.azure.com'
  location: 'global'
  tags: tags
}

// Private DNS Zone for Blob Storage
resource blobDnsZone 'Microsoft.Network/privateDnsZones@2020-06-01' = {
  name: 'privatelink.blob.${environment().suffixes.storage}'
  location: 'global'
  tags: tags
}

// ========================================
// VNet Links
// ========================================

// Link PostgreSQL DNS zone to VNet
resource postgresVnetLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2020-06-01' = {
  parent: postgresDnsZone
  name: '${vnetName}-postgres-link'
  location: 'global'
  tags: tags
  properties: {
    registrationEnabled: false
    virtualNetwork: {
      id: vnetId
    }
  }
}

// Link Blob DNS zone to VNet
resource blobVnetLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2020-06-01' = {
  parent: blobDnsZone
  name: '${vnetName}-blob-link'
  location: 'global'
  tags: tags
  properties: {
    registrationEnabled: false
    virtualNetwork: {
      id: vnetId
    }
  }
}

// ========================================
// Outputs
// ========================================

output postgresDnsZoneId string = postgresDnsZone.id
output blobDnsZoneId string = blobDnsZone.id
output postgresDnsZoneName string = postgresDnsZone.name
output blobDnsZoneName string = blobDnsZone.name
