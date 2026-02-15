// ============================================================================
// DICOM Service RBAC Assignment Module
// ============================================================================
//
// Assigns DICOM Data Owner role to a service principal
//
// Parameters:
// - workspaceName: Name of the healthcare workspace
// - dicomServiceName: Name of the DICOM service
// - servicePrincipalObjectId: Object ID of the service principal to grant access
//

@description('Name of the healthcare workspace')
param workspaceName string

@description('Name of the DICOM service')
param dicomServiceName string

@description('Object ID of the service principal (from app registration)')
param servicePrincipalObjectId string

// DICOM Data Owner role definition ID (built-in Azure role)
var dicomDataOwnerRoleId = '58a3b984-7adf-4c20-983a-32417c86fbc8'

// ============================================================================
// Reference to existing DICOM service
// ============================================================================

resource dicomService 'Microsoft.HealthcareApis/workspaces/dicomservices@2023-11-01' existing = {
  name: '${workspaceName}/${dicomServiceName}'
}

// ============================================================================
// Role Assignment
// ============================================================================

resource dicomRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: dicomService
  name: guid(dicomService.id, servicePrincipalObjectId, dicomDataOwnerRoleId)
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', dicomDataOwnerRoleId)
    principalId: servicePrincipalObjectId
    principalType: 'ServicePrincipal'
  }
}

// ============================================================================
// Outputs
// ============================================================================

@description('Role assignment ID')
output roleAssignmentId string = dicomRoleAssignment.id

@description('Role assignment name')
output roleAssignmentName string = dicomRoleAssignment.name
