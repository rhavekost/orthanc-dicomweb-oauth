using './main.bicep'

// Environment configuration
param environmentName = 'production'
param location = 'eastus'
param resourceGroupName = 'rg-orthanc-production'

// Networking configuration
param vnetAddressPrefix = '10.0.0.0/16'
param containerAppsSubnetPrefix = '10.0.1.0/24'
param privateEndpointsSubnetPrefix = '10.0.2.0/24'

// Container image configuration
param containerImage = 'myregistry.azurecr.io/orthanc-oauth:latest'
param containerRegistryName = 'myregistry'
param containerRegistryResourceGroup = 'rg-shared-services'

// DICOM service configuration
param dicomServiceUrl = 'https://workspace.dicom.azurehealthcareapis.com/v2/'
param dicomScope = 'https://dicom.healthcareapis.azure.com/.default'

// Database configuration
param postgresAdminUsername = 'orthanc_admin'
@secure()
param postgresAdminPassword = ''

// Orthanc admin credentials
param orthancUsername = 'admin'
@secure()
param orthancPassword = ''

// Enable/disable features
param enablePrivateEndpoints = true
param enableNetworkIsolation = true

// Tags
param tags = {
  Environment: 'Production'
  Project: 'Orthanc-OAuth'
  ManagedBy: 'Bicep'
  Compliance: 'HIPAA'
}
