// ============================================================================
// Healthcare Workspace Module
// ============================================================================
//
// Creates Azure Health Data Services workspace with DICOM service
//
// Parameters:
// - workspaceName: Name of the healthcare workspace
// - dicomServiceName: Name of the DICOM service
// - location: Azure region
// - publicNetworkAccess: Enable public access (Enabled/Disabled)
//
// Outputs:
// - workspaceId: Resource ID of the workspace
// - dicomServiceUrl: DICOM service endpoint URL
// - dicomServiceId: Resource ID of the DICOM service
//

@description('Name of the healthcare workspace (alphanumeric only, globally unique)')
param workspaceName string

@description('Name of the DICOM service within the workspace')
param dicomServiceName string

@description('Azure region for all resources')
param location string = resourceGroup().location

@description('Enable public network access')
@allowed([
  'Enabled'
  'Disabled'
])
param publicNetworkAccess string = 'Enabled'

@description('Tags to apply to all resources')
param tags object = {}

// ============================================================================
// Healthcare Workspace
// ============================================================================

resource workspace 'Microsoft.HealthcareApis/workspaces@2023-11-01' = {
  name: workspaceName
  location: location
  tags: tags
  properties: {
    publicNetworkAccess: publicNetworkAccess
  }
}

// ============================================================================
// DICOM Service
// ============================================================================

resource dicomService 'Microsoft.HealthcareApis/workspaces/dicomservices@2023-11-01' = {
  parent: workspace
  name: dicomServiceName
  location: location
  tags: tags
  properties: {
    authenticationConfiguration: {
      authority: 'https://login.microsoftonline.com/${tenant().tenantId}'
      audiences: [
        'https://dicom.healthcareapis.azure.com/'
      ]
    }
    publicNetworkAccess: publicNetworkAccess
    corsConfiguration: {
      origins: [
        '*'
      ]
      headers: [
        '*'
      ]
      methods: [
        'GET'
        'POST'
        'PUT'
        'DELETE'
        'OPTIONS'
      ]
      maxAge: 3600
      allowCredentials: false
    }
  }
}

// ============================================================================
// Outputs
// ============================================================================

@description('Resource ID of the healthcare workspace')
output workspaceId string = workspace.id

@description('Name of the healthcare workspace')
output workspaceName string = workspace.name

@description('DICOM service endpoint URL')
output dicomServiceUrl string = dicomService.properties.serviceUrl

@description('Resource ID of the DICOM service')
output dicomServiceId string = dicomService.id

@description('DICOM service name')
output dicomServiceName string = dicomService.name

@description('Authentication authority for DICOM service')
output dicomAuthority string = dicomService.properties.authenticationConfiguration.authority

@description('Authentication audiences for DICOM service')
output dicomAudiences array = dicomService.properties.authenticationConfiguration.audiences
