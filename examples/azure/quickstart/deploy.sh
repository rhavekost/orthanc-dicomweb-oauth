#!/bin/bash
set -e

# ============================================================================
# Orthanc OAuth Azure Quickstart Deployment Script
# ============================================================================
#
# This script deploys a complete Orthanc instance with OAuth authentication
# connected to Azure Health Data Services DICOM service.
#
# Prerequisites:
# - Azure CLI logged in (az login)
# - Docker Desktop running
# - deployment-params.json with configuration
# - app-registration.json with OAuth credentials
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PARAMS_FILE="$SCRIPT_DIR/deployment-params.json"
APP_REG_FILE="$SCRIPT_DIR/app-registration.json"
OUTPUT_FILE="$SCRIPT_DIR/deployment-output.json"

echo "============================================================================"
echo "Orthanc OAuth Azure Quickstart Deployment"
echo "============================================================================"
echo ""

# ============================================================================
# Step 1: Validate prerequisites
# ============================================================================

echo "→ Validating prerequisites..."

if [ ! -f "$PARAMS_FILE" ]; then
    echo "ERROR: deployment-params.json not found"
    echo "Please create it with required parameters"
    exit 1
fi

if [ ! -f "$APP_REG_FILE" ]; then
    echo "ERROR: app-registration.json not found"
    echo "Please run the app registration setup first"
    exit 1
fi

# Check Azure CLI login
if ! az account show &>/dev/null; then
    echo "ERROR: Not logged into Azure CLI"
    echo "Please run: az login"
    exit 1
fi

# Check Docker
if ! docker info &>/dev/null; then
    echo "ERROR: Docker is not running"
    echo "Please start Docker Desktop"
    exit 1
fi

echo "✓ Prerequisites validated"
echo ""

# ============================================================================
# Step 2: Load configuration
# ============================================================================

echo "→ Loading configuration..."

# Load deployment parameters
ENVIRONMENT_NAME=$(jq -r '.environmentName' "$PARAMS_FILE")
LOCATION=$(jq -r '.location' "$PARAMS_FILE")
RESOURCE_GROUP=$(jq -r '.resourceGroupName' "$PARAMS_FILE")
CONTAINER_IMAGE=$(jq -r '.containerImage' "$PARAMS_FILE")
CONTAINER_REGISTRY=$(jq -r '.containerRegistryName' "$PARAMS_FILE")
POSTGRES_ADMIN_USER=$(jq -r '.postgresAdminUsername' "$PARAMS_FILE")
POSTGRES_ADMIN_PASSWORD=$(jq -r '.postgresAdminPassword' "$PARAMS_FILE")
ORTHANC_USERNAME=$(jq -r '.orthancUsername' "$PARAMS_FILE")
ORTHANC_PASSWORD=$(jq -r '.orthancPassword' "$PARAMS_FILE")

# Load app registration details
TENANT_ID=$(jq -r '.tenantId' "$APP_REG_FILE")
OAUTH_CLIENT_ID=$(jq -r '.clientId' "$APP_REG_FILE")
OAUTH_CLIENT_SECRET=$(jq -r '.clientSecret' "$APP_REG_FILE")
SERVICE_PRINCIPAL_OBJECT_ID=$(jq -r '.servicePrincipalObjectId' "$APP_REG_FILE")

echo "  Environment: $ENVIRONMENT_NAME"
echo "  Location: $LOCATION"
echo "  Resource Group: $RESOURCE_GROUP"
echo "  Registry: $CONTAINER_REGISTRY"
echo ""

# ============================================================================
# Step 3: Get ACR credentials
# ============================================================================

echo "→ Getting Azure Container Registry credentials..."

ACR_PASSWORD=$(az acr credential show \
    --name "$CONTAINER_REGISTRY" \
    --query "passwords[0].value" \
    -o tsv)

if [ -z "$ACR_PASSWORD" ]; then
    echo "ERROR: Failed to get ACR password"
    exit 1
fi

echo "✓ ACR credentials retrieved"
echo ""

# ============================================================================
# Step 4: Build and push Docker image
# ============================================================================

echo "→ Building Docker image for linux/amd64..."
echo "  CRITICAL: Building for amd64 architecture (Azure Container Apps requirement)"
echo ""

# Navigate to project root (3 levels up from quickstart)
PROJECT_ROOT="$SCRIPT_DIR/../../.."
cd "$PROJECT_ROOT"

# Build with explicit platform for Azure deployment
docker buildx build \
    --platform linux/amd64 \
    -t "$CONTAINER_IMAGE" \
    -f examples/azure/quickstart/Dockerfile \
    --push \
    .

if [ $? -ne 0 ]; then
    echo "ERROR: Docker build failed"
    exit 1
fi

echo "✓ Docker image built and pushed"
echo ""

# Return to script directory
cd "$SCRIPT_DIR"

# ============================================================================
# Step 5: Deploy infrastructure
# ============================================================================

echo "→ Deploying Azure infrastructure..."
echo "  This includes:"
echo "    - Healthcare Workspace"
echo "    - DICOM Service"
echo "    - PostgreSQL Database"
echo "    - Storage Account"
echo "    - Container App"
echo "    - RBAC permissions"
echo ""

DEPLOYMENT_NAME="orthanc-${ENVIRONMENT_NAME}-$(date +%Y%m%d-%H%M%S)"

az deployment sub create \
    --name "$DEPLOYMENT_NAME" \
    --location "$LOCATION" \
    --template-file main.bicep \
    --parameters \
        environmentName="$ENVIRONMENT_NAME" \
        location="$LOCATION" \
        resourceGroupName="$RESOURCE_GROUP" \
        containerImage="$CONTAINER_IMAGE" \
        containerRegistryName="$CONTAINER_REGISTRY" \
        containerRegistryPassword="$ACR_PASSWORD" \
        tenantId="$TENANT_ID" \
        oauthClientId="$OAUTH_CLIENT_ID" \
        oauthClientSecret="$OAUTH_CLIENT_SECRET" \
        servicePrincipalObjectId="$SERVICE_PRINCIPAL_OBJECT_ID" \
        postgresAdminUsername="$POSTGRES_ADMIN_USER" \
        postgresAdminPassword="$POSTGRES_ADMIN_PASSWORD" \
        orthancUsername="$ORTHANC_USERNAME" \
        orthancPassword="$ORTHANC_PASSWORD" \
    --query properties.outputs \
    -o json > "$OUTPUT_FILE"

if [ $? -ne 0 ]; then
    echo "ERROR: Deployment failed"
    exit 1
fi

echo "✓ Infrastructure deployed"
echo ""

# ============================================================================
# Step 6: Display results
# ============================================================================

echo "============================================================================"
echo "DEPLOYMENT SUCCESSFUL"
echo "============================================================================"
echo ""

# Extract outputs
CONTAINER_APP_URL=$(jq -r '.containerAppUrl.value' "$OUTPUT_FILE")
DICOM_SERVICE_URL=$(jq -r '.dicomServiceUrl.value' "$OUTPUT_FILE")
DICOM_SCOPE=$(jq -r '.dicomScope.value' "$OUTPUT_FILE")
TOKEN_ENDPOINT=$(jq -r '.tokenEndpoint.value' "$OUTPUT_FILE")
WORKSPACE_NAME=$(jq -r '.healthcareWorkspaceName.value' "$OUTPUT_FILE")

echo "Orthanc Instance:"
echo "  URL: https://$CONTAINER_APP_URL"
echo "  Username: $ORTHANC_USERNAME"
echo "  Password: $ORTHANC_PASSWORD"
echo ""

echo "DICOM Service:"
echo "  Workspace: $WORKSPACE_NAME"
echo "  URL: $DICOM_SERVICE_URL"
echo "  Scope: $DICOM_SCOPE"
echo ""

echo "OAuth Configuration:"
echo "  Client ID: $OAUTH_CLIENT_ID"
echo "  Token Endpoint: $TOKEN_ENDPOINT"
echo "  Permissions: DICOM Data Owner (assigned)"
echo ""

echo "Next Steps:"
echo "  1. Open Orthanc: https://$CONTAINER_APP_URL"
echo "  2. Log in with the credentials above"
echo "  3. Navigate to DICOMweb servers"
echo "  4. Test connection to 'azure-dicom'"
echo ""

echo "Configuration saved to: $OUTPUT_FILE"
echo ""
echo "============================================================================"
