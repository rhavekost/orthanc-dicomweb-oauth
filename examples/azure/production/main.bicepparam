// Bicep Parameters File for Production Deployment
//
// This file provides type-safe parameter definitions for deploying Orthanc with OAuth
// to Azure using Bicep. It references main.bicep and provides production-ready values.
//
// REQUIRED CUSTOMIZATIONS:
// - containerImage: Replace YOUR_REGISTRY with your Azure Container Registry name
// - containerRegistryName: Replace YOUR_REGISTRY_NAME with your ACR name
// - containerRegistryResourceGroup: Replace YOUR_ACR_RESOURCE_GROUP with the resource group containing your ACR
// - dicomServiceUrl: Replace YOUR_WORKSPACE with your Azure Health Data Services workspace name
// - postgresAdminPassword: Provide via command line or leave empty to be prompted
// - orthancPassword: Provide via command line or leave empty to be prompted
//
// USAGE:
//   az deployment sub create \
//     --location eastus \
//     --template-file main.bicep \
//     --parameters main.bicepparam \
//     --parameters postgresAdminPassword='<value>' orthancPassword='<value>'

// NOTE: This parameter file requires main.bicep which will be created in Task 21.
// The parameter file is created first to define the contract for the main template.
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
param containerImage = 'YOUR_REGISTRY.azurecr.io/orthanc-oauth:latest'
param containerRegistryName = 'YOUR_REGISTRY_NAME'
param containerRegistryResourceGroup = 'YOUR_ACR_RESOURCE_GROUP'

// DICOM service configuration
param dicomServiceUrl = 'https://YOUR_WORKSPACE.dicom.azurehealthcareapis.com/v2/'
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
