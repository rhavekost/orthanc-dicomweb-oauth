// ========================================
// Container App Module with Managed Identity and VNet Integration
// ========================================

@description('The name of the Container App')
param containerAppName string

@description('The name of the Container Apps Environment')
param environmentName string

@description('The location for the Container App')
param location string

@description('The container image to deploy')
param containerImage string

@description('The ID of the Container Apps subnet')
param containerAppsSubnetId string

@description('Orthanc admin username')
param orthancUsername string

@description('Orthanc admin password')
@secure()
param orthancPassword string

@description('PostgreSQL connection string')
@secure()
param postgresConnectionString string

@description('Storage account name')
param storageAccountName string

@description('Storage container name')
param storageContainerName string

@description('DICOM service URL')
param dicomServiceUrl string

@description('Resource tags')
param tags object = {}

// ========================================
// Container Apps Environment
// ========================================

resource environment 'Microsoft.App/managedEnvironments@2023-05-01' = {
  name: environmentName
  location: location
  tags: tags
  properties: {
    vnetConfiguration: {
      infrastructureSubnetId: containerAppsSubnetId
      internal: false  // External ingress
    }
    zoneRedundant: false
  }
}

// ========================================
// Container App
// ========================================

resource containerApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: containerAppName
  location: location
  tags: tags
  identity: {
    type: 'SystemAssigned'  // Enable system-assigned managed identity
  }
  properties: {
    environmentId: environment.id
    configuration: {
      ingress: {
        external: true
        targetPort: 8042
        transport: 'http'
        allowInsecure: false
      }
      secrets: [
        {
          name: 'orthanc-password'
          value: orthancPassword
        }
        {
          name: 'postgres-connection-string'
          value: postgresConnectionString
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'orthanc-oauth'
          image: containerImage
          resources: {
            cpu: json('1.0')
            memory: '2Gi'
          }
          env: [
            {
              name: 'ORTHANC_USERNAME'
              value: orthancUsername
            }
            {
              name: 'ORTHANC_PASSWORD'
              secretRef: 'orthanc-password'
            }
            {
              name: 'POSTGRES_CONNECTION_STRING'
              secretRef: 'postgres-connection-string'
            }
            {
              name: 'AZURE_STORAGE_ACCOUNT'
              value: storageAccountName
            }
            {
              name: 'AZURE_STORAGE_CONTAINER'
              value: storageContainerName
            }
            {
              name: 'DICOM_SERVICE_URL'
              value: dicomServiceUrl
            }
            {
              name: 'USE_MANAGED_IDENTITY'
              value: 'true'
            }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 3
      }
    }
  }
}

// ========================================
// Outputs
// ========================================

output containerAppId string = containerApp.id
output containerAppName string = containerApp.name
output containerAppUrl string = containerApp.properties.configuration.ingress.fqdn
output containerAppPrincipalId string = containerApp.identity.principalId
output environmentId string = environment.id
