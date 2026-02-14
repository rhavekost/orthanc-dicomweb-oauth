using './main.bicep'

// Environment configuration
param environmentName = 'quickstart'
param location = 'eastus'
param resourceGroupName = 'rg-orthanc-quickstart'

// Container image configuration
param containerImage = 'myregistry.azurecr.io/orthanc-oauth:latest'
param containerRegistryName = 'myregistry'

// DICOM service configuration
param dicomServiceUrl = 'https://workspace.dicom.azurehealthcareapis.com/v2/'
param tenantId = '00000000-0000-0000-0000-000000000000'
param dicomScope = 'https://dicom.healthcareapis.azure.com/.default'

// OAuth client credentials
param oauthClientId = '00000000-0000-0000-0000-000000000000'
@secure()
param oauthClientSecret = ''

// Database configuration
param postgresAdminUsername = 'orthanc_admin'
@secure()
param postgresAdminPassword = ''

// Orthanc admin credentials
param orthancUsername = 'admin'
@secure()
param orthancPassword = ''

// Tags
param tags = {
  Environment: 'Quickstart'
  Project: 'Orthanc-OAuth'
  ManagedBy: 'Bicep'
}
