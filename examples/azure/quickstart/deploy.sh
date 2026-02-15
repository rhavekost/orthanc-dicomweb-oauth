#!/bin/bash
set -e

# ============================================================================
# Orthanc OAuth Azure Quickstart Deployment Script
# ============================================================================
#
# This script deploys a completely self-contained Orthanc instance with OAuth
# authentication in a brand new Azure subscription.
#
# Prerequisites:
# - Azure CLI logged in (az login)
# - Docker Desktop running
# - app-registration.json with OAuth credentials (or run setup-app-registration.sh)
#
# What gets deployed:
# - Azure Container Registry (created automatically)
# - Healthcare Workspace + DICOM Service
# - PostgreSQL Flexible Server
# - Storage Account with Blob Storage
# - Container Apps Environment
# - Container App running Orthanc with OAuth plugin
# - RBAC permissions
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PARAMS_FILE="$SCRIPT_DIR/deployment-params.json"
APP_REG_FILE="$SCRIPT_DIR/app-registration.json"
OUTPUT_FILE="$SCRIPT_DIR/deployment-output.json"

echo "============================================================================"
echo "Orthanc OAuth Azure Quickstart Deployment"
echo "Truly standalone - works on brand new Azure subscriptions"
echo "============================================================================"
echo ""

# ============================================================================
# Step 1: Validate prerequisites
# ============================================================================

echo "→ Step 1/7: Validating prerequisites..."

if [ ! -f "$PARAMS_FILE" ]; then
    echo "ERROR: deployment-params.json not found"
    echo "Please create it with required parameters"
    exit 1
fi

if [ ! -f "$APP_REG_FILE" ]; then
    echo "ERROR: app-registration.json not found"
    echo "Please run: ./scripts/setup-app-registration.sh"
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

echo "→ Step 2/7: Loading configuration..."

# Load deployment parameters
ENVIRONMENT_NAME=$(jq -r '.environmentName' "$PARAMS_FILE")
LOCATION=$(jq -r '.location' "$PARAMS_FILE")
RESOURCE_GROUP=$(jq -r '.resourceGroupName' "$PARAMS_FILE")
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
echo ""

# ============================================================================
# Step 3: Register Azure Resource Providers
# ============================================================================

echo "→ Step 3/7: Registering Azure resource providers..."
echo "  (Required for brand new subscriptions)"
echo ""

PROVIDERS=(
    "Microsoft.ContainerRegistry"
    "Microsoft.HealthcareApis"
    "Microsoft.Storage"
    "Microsoft.DBforPostgreSQL"
    "Microsoft.App"
    "Microsoft.OperationalInsights"
)

for provider in "${PROVIDERS[@]}"; do
    echo "  Checking $provider..."
    reg_state=$(az provider show --namespace "$provider" --query "registrationState" -o tsv 2>/dev/null || echo "NotRegistered")

    if [ "$reg_state" != "Registered" ]; then
        echo "    Registering $provider..."
        az provider register --namespace "$provider" --wait
        echo "    ✓ $provider registered"
    else
        echo "    ✓ $provider already registered"
    fi
done

echo ""
echo "✓ All resource providers registered"
echo ""

# ============================================================================
# Step 4: Deploy infrastructure (Phase 1: ACR + Infrastructure)
# ============================================================================

echo "→ Step 4/7: Deploying Azure infrastructure..."
echo "  This creates all resources including:"
echo "    - Azure Container Registry (new!)"
echo "    - Healthcare Workspace + DICOM Service"
echo "    - PostgreSQL Database"
echo "    - Storage Account"
echo "    - Container Apps Environment"
echo "    - Log Analytics"
echo ""
echo "  Note: Container App will be deployed in next phase after image push"
echo ""

DEPLOYMENT_NAME="orthanc-infra-${ENVIRONMENT_NAME}-$(date +%Y%m%d-%H%M%S)"

# PHASE 1: Deploy infrastructure WITHOUT Container App (image doesn't exist yet)
echo "  Phase 1: Deploying infrastructure (ACR, Healthcare, DB, Storage)..."
az deployment sub create \
    --name "$DEPLOYMENT_NAME" \
    --location "$LOCATION" \
    --template-file main.bicep \
    --parameters \
        environmentName="$ENVIRONMENT_NAME" \
        location="$LOCATION" \
        resourceGroupName="$RESOURCE_GROUP" \
        tenantId="$TENANT_ID" \
        oauthClientId="$OAUTH_CLIENT_ID" \
        oauthClientSecret="$OAUTH_CLIENT_SECRET" \
        servicePrincipalObjectId="$SERVICE_PRINCIPAL_OBJECT_ID" \
        postgresAdminUsername="$POSTGRES_ADMIN_USER" \
        postgresAdminPassword="$POSTGRES_ADMIN_PASSWORD" \
        orthancUsername="$ORTHANC_USERNAME" \
        orthancPassword="$ORTHANC_PASSWORD" \
        deployContainerApp=false \
    --query properties.outputs \
    -o json > "$OUTPUT_FILE"

if [ $? -ne 0 ]; then
    echo "ERROR: Infrastructure deployment failed"
    exit 1
fi

echo "✓ Infrastructure deployed"
echo ""

# ============================================================================
# Step 5: Get ACR details from deployment
# ============================================================================

echo "→ Step 5/7: Getting Container Registry details..."

# Extract ACR name from deployment outputs
CONTAINER_REGISTRY_NAME=$(jq -r '.containerRegistryName.value' "$OUTPUT_FILE")
CONTAINER_IMAGE="${CONTAINER_REGISTRY_NAME}.azurecr.io/orthanc-oauth:latest"

echo "  Registry: $CONTAINER_REGISTRY_NAME"
echo "  Image: $CONTAINER_IMAGE"
echo ""

# Get ACR credentials
ACR_PASSWORD=$(az acr credential show \
    --name "$CONTAINER_REGISTRY_NAME" \
    --query "passwords[0].value" \
    -o tsv)

if [ -z "$ACR_PASSWORD" ]; then
    echo "ERROR: Failed to get ACR password"
    exit 1
fi

echo "✓ Container Registry credentials retrieved"
echo ""

# ============================================================================
# Step 6: Build and push Docker image
# ============================================================================

echo "→ Step 6/7: Building and pushing Docker image..."
echo "  CRITICAL: Building for linux/amd64 (Azure Container Apps requirement)"
echo ""

# Login to Docker registry
echo "  Logging into ACR..."
echo "$ACR_PASSWORD" | docker login "${CONTAINER_REGISTRY_NAME}.azurecr.io" \
    --username "$CONTAINER_REGISTRY_NAME" \
    --password-stdin

if [ $? -ne 0 ]; then
    echo "ERROR: Docker login failed"
    exit 1
fi

# Navigate to project root
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
# Step 7: Deploy Container App (Phase 2)
# ============================================================================

echo "→ Step 7/7: Deploying Container App (now that image exists)..."
echo "  Phase 2: Creating Container App with the pushed image"
echo ""

DEPLOYMENT_NAME_PHASE2="orthanc-app-${ENVIRONMENT_NAME}-$(date +%Y%m%d-%H%M%S)"

az deployment sub create \
    --name "$DEPLOYMENT_NAME_PHASE2" \
    --location "$LOCATION" \
    --template-file main.bicep \
    --parameters \
        environmentName="$ENVIRONMENT_NAME" \
        location="$LOCATION" \
        resourceGroupName="$RESOURCE_GROUP" \
        tenantId="$TENANT_ID" \
        oauthClientId="$OAUTH_CLIENT_ID" \
        oauthClientSecret="$OAUTH_CLIENT_SECRET" \
        servicePrincipalObjectId="$SERVICE_PRINCIPAL_OBJECT_ID" \
        postgresAdminUsername="$POSTGRES_ADMIN_USER" \
        postgresAdminPassword="$POSTGRES_ADMIN_PASSWORD" \
        orthancUsername="$ORTHANC_USERNAME" \
        orthancPassword="$ORTHANC_PASSWORD" \
        deployContainerApp=true \
    --query properties.outputs \
    -o json > "$OUTPUT_FILE"

if [ $? -ne 0 ]; then
    echo "ERROR: Container App deployment failed"
    exit 1
fi

echo "✓ Container App deployed and running"
echo ""

# ============================================================================
# Step 8: Upload Sample DICOM Files (Optional)
# ============================================================================

# Extract Container App URL for uploading files
CONTAINER_APP_URL=$(jq -r '.containerAppUrl.value' "$OUTPUT_FILE")

echo "→ Step 8/8: Upload sample DICOM test files? (Optional)"
echo "  This will upload 3 sample CT images to your Orthanc instance"
echo ""
read -p "Upload test files? (Y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
    echo ""
    echo "Uploading sample DICOM files..."
    echo ""

    # Wait for Container App to be fully ready
    echo "  Waiting for Orthanc to be ready..."
    sleep 10

    SAMPLE_DIR="$SCRIPT_DIR/../test-data/sample-study"
    UPLOAD_COUNT=0
    UPLOAD_ERRORS=0

    for dicom_file in "$SAMPLE_DIR"/*.dcm; do
        if [ -f "$dicom_file" ]; then
            filename=$(basename "$dicom_file")
            echo "  Uploading $filename..."

            response=$(curl -s -w "\n%{http_code}" \
                -u "$ORTHANC_USERNAME:$ORTHANC_PASSWORD" \
                -X POST \
                "https://$CONTAINER_APP_URL/instances" \
                -H "Content-Type: application/dicom" \
                --data-binary "@$dicom_file" \
                2>&1)

            http_code=$(echo "$response" | tail -n 1)

            if [ "$http_code" = "200" ]; then
                echo "    ✓ $filename uploaded successfully"
                ((UPLOAD_COUNT++))
            else
                echo "    ✗ Failed to upload $filename (HTTP $http_code)"
                ((UPLOAD_ERRORS++))
            fi
        fi
    done

    echo ""
    if [ $UPLOAD_COUNT -gt 0 ]; then
        echo "✓ Uploaded $UPLOAD_COUNT sample DICOM file(s)"
        [ $UPLOAD_ERRORS -gt 0 ] && echo "⚠ Failed to upload $UPLOAD_ERRORS file(s)"
    else
        echo "⚠ No DICOM files were uploaded"
    fi
else
    echo "Skipping test file upload"
fi

echo ""

# ============================================================================
# Display results
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

echo "Container Registry:"
echo "  Name: $CONTAINER_REGISTRY_NAME"
echo "  Image: $CONTAINER_IMAGE"
echo ""

echo "Next Steps:"
echo "  1. Wait 2-3 minutes for Container App to start"
echo "  2. Open Orthanc: https://$CONTAINER_APP_URL"
echo "  3. Log in with the credentials above"
echo "  4. Navigate to DICOMweb servers"
echo "  5. Test connection to 'azure-dicom'"
echo ""

echo "Troubleshooting:"
echo "  View logs: az containerapp logs show --name orthanc-${ENVIRONMENT_NAME}-app --resource-group $RESOURCE_GROUP --follow"
echo ""

echo "Configuration saved to: $OUTPUT_FILE"
echo ""
echo "============================================================================"
