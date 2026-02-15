// ========================================
// PostgreSQL Configuration Module
// ========================================
// This module configures PostgreSQL settings and extensions
// Must be deployed at resource group scope

targetScope = 'resourceGroup'

@description('The name of the PostgreSQL server')
param postgresServerName string

// ========================================
// PostgreSQL Configuration for Orthanc
// ========================================

// Reference to the deployed PostgreSQL server
resource postgresServer 'Microsoft.DBforPostgreSQL/flexibleServers@2023-06-01-preview' existing = {
  name: postgresServerName
}

// Disable SSL requirement for simplified connectivity
// Note: For production, consider enabling SSL with proper certificate configuration
resource postgresSSLConfig 'Microsoft.DBforPostgreSQL/flexibleServers/configurations@2023-06-01-preview' = {
  name: 'require_secure_transport'
  parent: postgresServer
  properties: {
    value: 'off'
    source: 'user-override'
  }
}

// Enable PostgreSQL extensions required by Orthanc
// pg_trgm: Text search capabilities for DICOM metadata
// uuid-ossp: UUID generation for database records
resource postgresExtensions 'Microsoft.DBforPostgreSQL/flexibleServers/configurations@2023-06-01-preview' = {
  name: 'azure.extensions'
  parent: postgresServer
  properties: {
    value: 'pg_trgm,uuid-ossp'
    source: 'user-override'
  }
  dependsOn: [
    postgresSSLConfig
  ]
}
