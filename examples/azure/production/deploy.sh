#!/bin/bash
set -e

# Production Deployment Script for Orthanc with OAuth
# This script deploys the full production environment including:
# - Private VNet with subnets
# - Azure Container Registry
# - PostgreSQL Flexible Server
# - Azure Storage Account
# - Azure Container Apps (with VNet integration)
# - Azure Healthcare APIs DICOM service

echo "=========================================="
echo "Orthanc OAuth Production Deployment"
echo "=========================================="
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
echo "Generated secure passwords for Orthanc and PostgreSQL"
echo ""

#############################################
# Phase 2: Deploy Network Infrastructure
#############################################
echo "Phase 2: Deploy Network Infrastructure"
echo "----------------------------------------"

# Deploy using subscription-level deployment with secure parameter file
echo "Starting Azure deployment..."
DEPLOYMENT_NAME="orthanc-oauth-${ENV_NAME}-$(date +%Y%m%d-%H%M%S)"

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
    "orthancUsername": {"value": "$ORTHANC_USERNAME"},
    "orthancPassword": {"value": "$ORTHANC_PASSWORD"},
    "postgresAdminUsername": {"value": "$POSTGRES_USERNAME"},
    "postgresAdminPassword": {"value": "$POSTGRES_PASSWORD"}
  }
}
EOF

az deployment sub create \
  --name "$DEPLOYMENT_NAME" \
  --location "$LOCATION" \
  --template-file "$SCRIPT_DIR/main.bicep" \
  --parameters "@$PARAM_FILE" \
  -o json > "$SCRIPT_DIR/deployment-output.json"

# Check deployment status
if [ $? -ne 0 ]; then
  echo "ERROR: Azure deployment failed"
  exit 1
fi

echo "Azure infrastructure deployment completed successfully"
echo ""

#############################################
# Phase 3: Extract Deployment Details
#############################################
echo "Phase 3: Extract Deployment Details"
echo "----------------------------------------"

# Extract all critical outputs using jq
ACR_NAME=$(jq -r '.properties.outputs.containerRegistryName.value' "$SCRIPT_DIR/deployment-output.json")
ACR_LOGIN_SERVER=$(jq -r '.properties.outputs.containerRegistryLoginServer.value' "$SCRIPT_DIR/deployment-output.json")
CONTAINER_APP_URL=$(jq -r '.properties.outputs.containerAppUrl.value' "$SCRIPT_DIR/deployment-output.json")
DICOM_URL=$(jq -r '.properties.outputs.dicomServiceUrl.value' "$SCRIPT_DIR/deployment-output.json")
POSTGRES_FQDN=$(jq -r '.properties.outputs.postgresServerFqdn.value' "$SCRIPT_DIR/deployment-output.json")
STORAGE_NAME=$(jq -r '.properties.outputs.storageAccountName.value' "$SCRIPT_DIR/deployment-output.json")
RESOURCE_GROUP=$(jq -r '.properties.outputs.resourceGroupName.value' "$SCRIPT_DIR/deployment-output.json")
VNET_ID=$(jq -r '.properties.outputs.vnetId.value' "$SCRIPT_DIR/deployment-output.json")

# Validate all critical outputs
for var in ACR_NAME ACR_LOGIN_SERVER CONTAINER_APP_URL DICOM_URL; do
  eval value=\$$var
  if [ -z "$value" ] || [ "$value" = "null" ]; then
    echo "ERROR: Failed to extract $var from deployment output"
    exit 1
  fi
done

echo "Container Registry Name: $ACR_NAME"
echo "Container Registry Server: $ACR_LOGIN_SERVER"
echo "Container App URL: $CONTAINER_APP_URL"
echo "DICOM Service URL: $DICOM_URL"
echo "PostgreSQL Server FQDN: $POSTGRES_FQDN"
echo "Storage Account Name: $STORAGE_NAME"
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
# Phase 5: Restart Container App
#############################################
echo "Phase 5: Restart Container App"
echo "----------------------------------------"

# Find container app name
CONTAINER_APP_NAME=$(az containerapp list \
  --resource-group "$RG_NAME" \
  --query "[0].name" \
  --output tsv)

if [ -z "$CONTAINER_APP_NAME" ]; then
  echo "ERROR: Failed to find Container App in resource group $RG_NAME"
  exit 1
fi

echo "Container App Name: $CONTAINER_APP_NAME"

# Restart container app to pull new image
echo "Restarting Container App to pull new image..."
az containerapp revision restart \
  --name "$CONTAINER_APP_NAME" \
  --resource-group "$RG_NAME" \
  --revision "$(az containerapp revision list \
    --name "$CONTAINER_APP_NAME" \
    --resource-group "$RG_NAME" \
    --query "[0].name" \
    --output tsv)"

if [ $? -ne 0 ]; then
  echo "WARNING: Container App restart failed, but deployment may still be successful"
fi

echo ""

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
echo "Credentials saved to: $SCRIPT_DIR/deployment-output.json"
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
