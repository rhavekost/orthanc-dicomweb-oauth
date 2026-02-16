#!/bin/bash
set -e

# Production Deployment Script for Orthanc with OAuth
# Split Deployment Approach:
# - Phase 2: Deploy Infrastructure (ACR, VNet, PostgreSQL, Storage, Healthcare APIs)
# - Phase 3: Build and Push Docker Image
# - Phase 4: Deploy Container App (after image exists in ACR)

echo "=========================================="
echo "Orthanc OAuth Production Deployment"
echo "=========================================="
echo ""

#############################################
# Prerequisites: Register Resource Providers
#############################################
echo "Prerequisites: Checking Resource Providers"
echo "----------------------------------------"

# Required resource providers for this deployment
REQUIRED_PROVIDERS="Microsoft.App Microsoft.ContainerService Microsoft.HealthcareApis Microsoft.Network Microsoft.Storage Microsoft.ContainerRegistry Microsoft.DBforPostgreSQL"

for PROVIDER in $REQUIRED_PROVIDERS; do
  echo "Checking $PROVIDER..."
  # Check registration status
  STATUS=$(az provider show --namespace "$PROVIDER" --query "registrationState" -o tsv 2>/dev/null || echo "NotFound")

  if [ "$STATUS" != "Registered" ]; then
    echo "  Registering $PROVIDER (this may take a few minutes)..."
    az provider register --namespace "$PROVIDER" --wait
    echo "  ✓ $PROVIDER registered"
  else
    echo "  ✓ $PROVIDER already registered"
  fi
done

echo "All required resource providers are registered"
echo ""

#############################################
# Phase 1: Configuration
#############################################
echo "Phase 1: Configuration"
echo "----------------------------------------"

# Environment variables with defaults
ENV_NAME="${ENV_NAME:-production}"
LOCATION="${LOCATION:-westus2}"
RG_NAME="rg-orthanc-oauth-${ENV_NAME}"

# Get the directory where this script is located (needed for credential storage)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Load existing credentials if available (idempotent deployment)
DETAILS_FILE="$SCRIPT_DIR/deployment-details.json"
if [ -f "$DETAILS_FILE" ]; then
  echo "Found existing deployment - reusing credentials"
  ORTHANC_PASSWORD=$(jq -r '.orthancPassword' "$DETAILS_FILE")
  POSTGRES_PASSWORD=$(jq -r '.postgresPassword' "$DETAILS_FILE")
else
  echo "Generating new credentials"
  ORTHANC_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
  POSTGRES_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)

  # Save for future runs
  jq -n \
    --arg op "$ORTHANC_PASSWORD" \
    --arg pp "$POSTGRES_PASSWORD" \
    '{orthancPassword: $op, postgresPassword: $pp}' \
    > "$DETAILS_FILE"

  echo "Credentials saved to $DETAILS_FILE"
fi

# Fixed usernames
ORTHANC_USERNAME="orthanc"
POSTGRES_USERNAME="orthancadmin"

# Display configuration
echo "Environment Name: $ENV_NAME"
echo "Location: $LOCATION"
echo "Resource Group: $RG_NAME"
echo "Orthanc Username: $ORTHANC_USERNAME"
echo "PostgreSQL Username: $POSTGRES_USERNAME"
echo ""
echo "Secure passwords loaded from $DETAILS_FILE"
echo ""

#############################################
# Phase 2: Deploy Infrastructure Only
#############################################
echo "Phase 2: Deploy Infrastructure (VNet, ACR, PostgreSQL, Storage, Healthcare APIs)"
echo "----------------------------------------"

# Deploy infrastructure without Container App
echo "Starting infrastructure deployment..."
DEPLOYMENT_NAME="orthanc-oauth-infra-${ENV_NAME}-$(date +%Y%m%d-%H%M%S)"

# Create temporary parameter file to avoid password exposure in process list
PARAM_FILE=$(mktemp)
trap 'rm -f "$PARAM_FILE"' EXIT

cat > "$PARAM_FILE" <<EOF
{
  "\$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentParameters.json#",
  "contentVersion": "1.0.0.0",
  "parameters": {
    "environmentName": {"value": "$ENV_NAME"},
    "location": {"value": "$LOCATION"},
    "resourceGroupName": {"value": "$RG_NAME"},
    "postgresAdminUsername": {"value": "$POSTGRES_USERNAME"},
    "postgresAdminPassword": {"value": "$POSTGRES_PASSWORD"}
  }
}
EOF

az deployment sub create \
  --name "$DEPLOYMENT_NAME" \
  --location "$LOCATION" \
  --template-file "$SCRIPT_DIR/main-infra.bicep" \
  --parameters "@$PARAM_FILE" \
  -o json > "$SCRIPT_DIR/infrastructure-output.json"

# Check deployment status
if [ $? -ne 0 ]; then
  echo "ERROR: Infrastructure deployment failed"
  exit 1
fi

echo "Infrastructure deployment completed successfully"
echo ""

#############################################
# Phase 3: Extract Infrastructure Outputs
#############################################
echo "Phase 3: Extract Infrastructure Outputs"
echo "----------------------------------------"

# Extract all critical outputs using jq
ACR_NAME=$(jq -r '.properties.outputs.containerRegistryName.value' "$SCRIPT_DIR/infrastructure-output.json")
ACR_LOGIN_SERVER=$(jq -r '.properties.outputs.containerRegistryLoginServer.value' "$SCRIPT_DIR/infrastructure-output.json")
ACR_USERNAME=$(jq -r '.properties.outputs.containerRegistryAdminUsername.value' "$SCRIPT_DIR/infrastructure-output.json")
ACR_PASSWORD=$(jq -r '.properties.outputs.containerRegistryAdminPassword.value' "$SCRIPT_DIR/infrastructure-output.json")
DICOM_URL=$(jq -r '.properties.outputs.dicomServiceUrl.value' "$SCRIPT_DIR/infrastructure-output.json")
DICOM_ID=$(jq -r '.properties.outputs.dicomServiceId.value' "$SCRIPT_DIR/infrastructure-output.json")
POSTGRES_FQDN=$(jq -r '.properties.outputs.postgresServerFqdn.value' "$SCRIPT_DIR/infrastructure-output.json")
POSTGRES_NAME=$(jq -r '.properties.outputs.postgresServerName.value' "$SCRIPT_DIR/infrastructure-output.json")
STORAGE_NAME=$(jq -r '.properties.outputs.storageAccountName.value' "$SCRIPT_DIR/infrastructure-output.json")
STORAGE_ID=$(jq -r '.properties.outputs.storageAccountId.value' "$SCRIPT_DIR/infrastructure-output.json")
STORAGE_CONTAINER=$(jq -r '.properties.outputs.storageContainerName.value' "$SCRIPT_DIR/infrastructure-output.json")
RESOURCE_GROUP=$(jq -r '.properties.outputs.resourceGroupName.value' "$SCRIPT_DIR/infrastructure-output.json")
VNET_ID=$(jq -r '.properties.outputs.vnetId.value' "$SCRIPT_DIR/infrastructure-output.json")
CONTAINER_APPS_SUBNET_ID=$(jq -r '.properties.outputs.containerAppsSubnetId.value' "$SCRIPT_DIR/infrastructure-output.json")

# Validate all critical outputs
for var in ACR_NAME ACR_LOGIN_SERVER DICOM_URL POSTGRES_NAME STORAGE_NAME; do
  eval value=\$$var
  if [ -z "$value" ] || [ "$value" = "null" ]; then
    echo "ERROR: Failed to extract $var from infrastructure output"
    exit 1
  fi
done

echo "Container Registry: $ACR_NAME ($ACR_LOGIN_SERVER)"
echo "DICOM Service: $DICOM_URL"
echo "PostgreSQL Server: $POSTGRES_FQDN"
echo "Storage Account: $STORAGE_NAME"
echo "Resource Group: $RESOURCE_GROUP"
echo ""

#############################################
# Phase 4: Build and Push Docker Image
#############################################
echo "Phase 4: Build and Push Docker Image"
echo "----------------------------------------"

# Login to ACR
echo "Logging in to Azure Container Registry..."
az acr login --name "$ACR_NAME"

# Build Docker image for linux/amd64 platform (Azure Container Apps requirement)
# Use production Dockerfile which includes azure-identity dependency
echo "Building Docker image for linux/amd64 platform..."
IMAGE_TAG="${ACR_LOGIN_SERVER}/orthanc-oauth:latest"

# Navigate to repository root (3 levels up from script directory)
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

docker buildx build \
  --platform linux/amd64 \
  --file "$SCRIPT_DIR/Dockerfile" \
  --tag "$IMAGE_TAG" \
  --push \
  "$REPO_ROOT"

if [ $? -ne 0 ]; then
  echo "ERROR: Docker image build and push failed"
  exit 1
fi

echo "Docker image built and pushed successfully: $IMAGE_TAG"
echo ""

#############################################
# Phase 5: Deploy Container App
#############################################
echo "Phase 5: Deploy Container App + RBAC"
echo "----------------------------------------"

echo "Deploying Container App to resource group $RESOURCE_GROUP..."
APP_DEPLOYMENT_NAME="orthanc-oauth-app-${ENV_NAME}-$(date +%Y%m%d-%H%M%S)"

# Create parameter file for Container App deployment
APP_PARAM_FILE=$(mktemp)
trap 'rm -f "$APP_PARAM_FILE"' EXIT

cat > "$APP_PARAM_FILE" <<EOF
{
  "\$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentParameters.json#",
  "contentVersion": "1.0.0.0",
  "parameters": {
    "environmentName": {"value": "$ENV_NAME"},
    "location": {"value": "$LOCATION"},
    "orthancUsername": {"value": "$ORTHANC_USERNAME"},
    "orthancPassword": {"value": "$ORTHANC_PASSWORD"},
    "postgresAdminUsername": {"value": "$POSTGRES_USERNAME"},
    "postgresAdminPassword": {"value": "$POSTGRES_PASSWORD"},
    "containerRegistryLoginServer": {"value": "$ACR_LOGIN_SERVER"},
    "containerRegistryAdminUsername": {"value": "$ACR_USERNAME"},
    "containerRegistryAdminPassword": {"value": "$ACR_PASSWORD"},
    "containerRegistryId": {"value": "/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.ContainerRegistry/registries/$ACR_NAME"},
    "containerAppsSubnetId": {"value": "$CONTAINER_APPS_SUBNET_ID"},
    "storageAccountName": {"value": "$STORAGE_NAME"},
    "storageContainerName": {"value": "$STORAGE_CONTAINER"},
    "storageAccountId": {"value": "$STORAGE_ID"},
    "dicomServiceUrl": {"value": "$DICOM_URL"},
    "dicomServiceId": {"value": "$DICOM_ID"},
    "postgresServerName": {"value": "$POSTGRES_NAME"}
  }
}
EOF

az deployment group create \
  --name "$APP_DEPLOYMENT_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --template-file "$SCRIPT_DIR/main-app.bicep" \
  --parameters "@$APP_PARAM_FILE" \
  -o json > "$SCRIPT_DIR/app-output.json"

if [ $? -ne 0 ]; then
  echo "ERROR: Container App deployment failed"
  exit 1
fi

echo "Container App deployment completed successfully"
echo ""

# Extract Container App URL
CONTAINER_APP_URL=$(jq -r '.properties.outputs.containerAppUrl.value' "$SCRIPT_DIR/app-output.json")

#############################################
# Deployment Complete
#############################################
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
echo "Access Information:"
echo "  URL: https://$CONTAINER_APP_URL"
echo "  Username: $ORTHANC_USERNAME"
echo "  Password: $ORTHANC_PASSWORD"
echo ""
echo "Infrastructure Details:"
echo "  Resource Group: $RESOURCE_GROUP"
echo "  Container Registry: $ACR_NAME"
echo "  PostgreSQL Server: $POSTGRES_FQDN"
echo "  DICOM Service: $DICOM_URL"
echo "  Storage Account: $STORAGE_NAME"
echo ""
echo "Credentials saved to: $SCRIPT_DIR/deployment-details.json"
echo ""
echo "IMPORTANT: Save these credentials securely!"
echo "  Orthanc Username: $ORTHANC_USERNAME"
echo "  Orthanc Password: $ORTHANC_PASSWORD"
echo "  PostgreSQL Username: $POSTGRES_USERNAME"
echo "  PostgreSQL Password: $POSTGRES_PASSWORD"
echo ""
echo "To access Orthanc:"
echo "  curl -u $ORTHANC_USERNAME:$ORTHANC_PASSWORD https://$CONTAINER_APP_URL/app/explorer.html"
echo ""
