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

# Generate secure random passwords
ORTHANC_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
POSTGRES_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)

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

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Deploy using subscription-level deployment
echo "Starting Azure deployment..."
az deployment sub create \
  --name "orthanc-oauth-${ENV_NAME}-$(date +%Y%m%d-%H%M%S)" \
  --location "$LOCATION" \
  --template-file "$SCRIPT_DIR/main.bicep" \
  --parameters environmentName="$ENV_NAME" \
  --parameters location="$LOCATION" \
  --parameters resourceGroupName="$RG_NAME" \
  --parameters orthancUsername="$ORTHANC_USERNAME" \
  --parameters orthancPassword="$ORTHANC_PASSWORD" \
  --parameters postgresAdminUsername="$POSTGRES_USERNAME" \
  --parameters postgresAdminPassword="$POSTGRES_PASSWORD" \
  --output json > "$SCRIPT_DIR/deployment-output.json"

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

# Extract outputs using jq
ACR_NAME=$(jq -r '.properties.outputs.containerRegistryName.value' "$SCRIPT_DIR/deployment-output.json")
ACR_LOGIN_SERVER=$(jq -r '.properties.outputs.containerRegistryLoginServer.value' "$SCRIPT_DIR/deployment-output.json")
CONTAINER_APP_URL=$(jq -r '.properties.outputs.containerAppUrl.value' "$SCRIPT_DIR/deployment-output.json")

# Validate extracted values
if [ -z "$ACR_NAME" ] || [ "$ACR_NAME" = "null" ]; then
  echo "ERROR: Failed to extract Container Registry name from deployment output"
  exit 1
fi

if [ -z "$ACR_LOGIN_SERVER" ] || [ "$ACR_LOGIN_SERVER" = "null" ]; then
  echo "ERROR: Failed to extract Container Registry login server from deployment output"
  exit 1
fi

if [ -z "$CONTAINER_APP_URL" ] || [ "$CONTAINER_APP_URL" = "null" ]; then
  echo "ERROR: Failed to extract Container App URL from deployment output"
  exit 1
fi

echo "Container Registry Name: $ACR_NAME"
echo "Container Registry Server: $ACR_LOGIN_SERVER"
echo "Container App URL: $CONTAINER_APP_URL"
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
