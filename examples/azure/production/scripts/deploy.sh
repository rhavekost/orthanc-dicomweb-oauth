#!/usr/bin/env bash
set -euo pipefail

# ========================================
# Deploy Orthanc OAuth Production to Azure
# ========================================
#
# This script deploys the production Orthanc OAuth setup to Azure
# with VNet integration and managed identity.
#
# Prerequisites:
# - Azure CLI 2.50+
# - Docker (for building custom image)
# - Azure Container Registry
# - Permissions to assign roles
#
# Usage:
#   ./deploy.sh --resource-group rg-orthanc-prod --location eastus --registry myregistry
#

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
RESOURCE_GROUP=""
LOCATION="eastus"
ENVIRONMENT_NAME="production"
PARAMETERS_FILE="parameters.json"
BUILD_IMAGE=true
CONTAINER_REGISTRY=""
CONTAINER_REGISTRY_RG=""
IMAGE_TAG="latest"
VNET_ADDRESS_PREFIX="10.0.0.0/16"
CONTAINER_APPS_SUBNET="10.0.1.0/24"
PRIVATE_ENDPOINTS_SUBNET="10.0.2.0/24"

# ========================================
# Functions
# ========================================

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Deploy Orthanc OAuth production setup to Azure with VNet and managed identity.

OPTIONS:
    -g, --resource-group NAME       Resource group name (required)
    -l, --location LOCATION         Azure region (default: eastus)
    -e, --environment NAME          Environment name (default: production)
    -p, --parameters FILE           Parameters JSON file (default: parameters.json)
    -r, --registry NAME             Azure Container Registry name (required if building)
    -R, --registry-rg NAME          ACR resource group (default: same as resource group)
    -t, --tag TAG                   Container image tag (default: latest)
    --vnet-prefix PREFIX            VNet address prefix (default: 10.0.0.0/16)
    --container-subnet PREFIX       Container Apps subnet (default: 10.0.1.0/24)
    --private-subnet PREFIX         Private Endpoints subnet (default: 10.0.2.0/24)
    --no-build                      Skip building container image
    -h, --help                      Show this help message

EXAMPLE:
    $0 --resource-group rg-orthanc-prod --registry myregistry --registry-rg rg-shared

EOF
}

# ========================================
# Parse Arguments
# ========================================

while [[ $# -gt 0 ]]; do
    case $1 in
        -g|--resource-group)
            RESOURCE_GROUP="$2"
            shift 2
            ;;
        -l|--location)
            LOCATION="$2"
            shift 2
            ;;
        -e|--environment)
            ENVIRONMENT_NAME="$2"
            shift 2
            ;;
        -p|--parameters)
            PARAMETERS_FILE="$2"
            shift 2
            ;;
        -r|--registry)
            CONTAINER_REGISTRY="$2"
            shift 2
            ;;
        -R|--registry-rg)
            CONTAINER_REGISTRY_RG="$2"
            shift 2
            ;;
        -t|--tag)
            IMAGE_TAG="$2"
            shift 2
            ;;
        --vnet-prefix)
            VNET_ADDRESS_PREFIX="$2"
            shift 2
            ;;
        --container-subnet)
            CONTAINER_APPS_SUBNET="$2"
            shift 2
            ;;
        --private-subnet)
            PRIVATE_ENDPOINTS_SUBNET="$2"
            shift 2
            ;;
        --no-build)
            BUILD_IMAGE=false
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Validate required parameters
if [[ -z "$RESOURCE_GROUP" ]]; then
    log_error "Resource group is required"
    show_usage
    exit 1
fi

if [[ "$BUILD_IMAGE" == true && -z "$CONTAINER_REGISTRY" ]]; then
    log_error "Container registry is required when building image"
    show_usage
    exit 1
fi

# Default ACR RG to same as deployment RG if not specified
if [[ -z "$CONTAINER_REGISTRY_RG" ]]; then
    CONTAINER_REGISTRY_RG="$RESOURCE_GROUP"
fi

# ========================================
# Main Script
# ========================================

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

log_step "Step 1/7: Validating prerequisites"

# Check Azure CLI
az version --output tsv > /dev/null 2>&1 || {
    log_error "Azure CLI not found. Please install Azure CLI 2.50+"
    exit 1
}

# Check logged in
az account show > /dev/null 2>&1 || {
    log_error "Not logged in to Azure. Run 'az login' first."
    exit 1
}

SUBSCRIPTION_ID=$(az account show --query id -o tsv)
log_info "Using subscription: $SUBSCRIPTION_ID"

# ========================================
# Build and Push Container Image
# ========================================

if [[ "$BUILD_IMAGE" == true ]]; then
    log_step "Step 2/7: Building and pushing container image"

    CONTAINER_IMAGE="${CONTAINER_REGISTRY}.azurecr.io/orthanc-oauth:${IMAGE_TAG}"

    # Login to ACR
    log_info "Logging into Azure Container Registry: $CONTAINER_REGISTRY"
    az acr login --name "$CONTAINER_REGISTRY"

    # Build image for linux/amd64 (required for Azure Container Apps)
    log_info "Building Docker image: $CONTAINER_IMAGE"
    docker buildx build \
        --platform linux/amd64 \
        -t "$CONTAINER_IMAGE" \
        -f examples/azure/quickstart/Dockerfile \
        --push \
        "$REPO_ROOT"

    log_info "Image pushed: $CONTAINER_IMAGE"
else
    log_step "Step 2/7: Skipping image build (--no-build specified)"

    # Read from parameters file if exists
    if [[ -f "$PARAMETERS_FILE" ]]; then
        CONTAINER_IMAGE=$(jq -r '.parameters.containerImage.value' "$PARAMETERS_FILE")
        log_info "Using existing image: $CONTAINER_IMAGE"
    else
        log_error "No parameters file found and --no-build specified"
        exit 1
    fi
fi

# ========================================
# Create Resource Group
# ========================================

log_step "Step 3/7: Creating resource group"

if az group show --name "$RESOURCE_GROUP" &> /dev/null; then
    log_info "Resource group already exists: $RESOURCE_GROUP"
else
    log_info "Creating resource group: $RESOURCE_GROUP"
    az group create --name "$RESOURCE_GROUP" --location "$LOCATION"
fi

# ========================================
# Generate Deployment Parameters
# ========================================

log_step "Step 4/7: Generating deployment parameters"

# Read DICOM service URL from parameters file
DICOM_SERVICE_URL=$(jq -r '.parameters.dicomServiceUrl.value' "$PARAMETERS_FILE")

# Generate secure passwords
POSTGRES_PASSWORD=$(openssl rand -base64 32)
ORTHANC_PASSWORD=$(openssl rand -base64 24)

# Create deployment parameters
cat > deployment-params.json << EOF
{
  "environmentName": "$ENVIRONMENT_NAME",
  "location": "$LOCATION",
  "resourceGroupName": "$RESOURCE_GROUP",
  "vnetAddressPrefix": "$VNET_ADDRESS_PREFIX",
  "containerAppsSubnetPrefix": "$CONTAINER_APPS_SUBNET",
  "privateEndpointsSubnetPrefix": "$PRIVATE_ENDPOINTS_SUBNET",
  "containerImage": "$CONTAINER_IMAGE",
  "containerRegistryName": "$CONTAINER_REGISTRY",
  "containerRegistryResourceGroup": "$CONTAINER_REGISTRY_RG",
  "dicomServiceUrl": "$DICOM_SERVICE_URL",
  "dicomScope": "https://dicom.healthcareapis.azure.com/.default",
  "postgresAdminUsername": "orthanc_admin",
  "postgresAdminPassword": "$POSTGRES_PASSWORD",
  "orthancUsername": "admin",
  "orthancPassword": "$ORTHANC_PASSWORD",
  "enablePrivateEndpoints": true,
  "enableNetworkIsolation": true
}
EOF

log_info "Deployment parameters generated"

# ========================================
# Deploy Bicep Template
# ========================================

log_step "Step 5/7: Deploying Azure resources with Bicep"

DEPLOYMENT_NAME="orthanc-production-$(date +%Y%m%d-%H%M%S)"

log_info "Starting deployment: $DEPLOYMENT_NAME"

az deployment sub create \
    --name "$DEPLOYMENT_NAME" \
    --location "$LOCATION" \
    --template-file "$SCRIPT_DIR/../main.bicep" \
    --parameters @deployment-params.json \
    --output json > deployment-output.json

log_info "Deployment complete"

# ========================================
# Extract Managed Identity Principal ID
# ========================================

log_step "Step 6/7: Configuring managed identity permissions"

MANAGED_IDENTITY_ID=$(jq -r '.properties.outputs.containerAppIdentityPrincipalId.value' deployment-output.json)

log_info "Container App Managed Identity: $MANAGED_IDENTITY_ID"

# Note: DICOM Data Owner role assignment should be done manually or via separate script
# as it requires the DICOM service resource ID

log_warn "IMPORTANT: Grant DICOM Data Owner role to managed identity:"
log_warn "  az role assignment create \\"
log_warn "    --assignee $MANAGED_IDENTITY_ID \\"
log_warn "    --role 'DICOM Data Owner' \\"
log_warn "    --scope /subscriptions/$SUBSCRIPTION_ID/resourceGroups/YOUR_DICOM_RG/providers/Microsoft.HealthcareApis/workspaces/YOUR_WORKSPACE"

# ========================================
# Display Outputs
# ========================================

log_step "Step 7/7: Deployment summary"

CONTAINER_APP_URL=$(jq -r '.properties.outputs.containerAppUrl.value' deployment-output.json)
POSTGRES_FQDN=$(jq -r '.properties.outputs.postgresServerFqdn.value' deployment-output.json)
STORAGE_ACCOUNT=$(jq -r '.properties.outputs.storageAccountName.value' deployment-output.json)
VNET_NAME=$(jq -r '.properties.outputs.vnetName.value' deployment-output.json)

cat << EOF

${GREEN}✓ Deployment successful!${NC}

Resource Group: $RESOURCE_GROUP
Location: $LOCATION

Resources deployed:
  - VNet: $VNET_NAME
  - Container App: https://$CONTAINER_APP_URL
  - PostgreSQL: $POSTGRES_FQDN (private endpoint)
  - Storage Account: $STORAGE_ACCOUNT (private endpoint)

Authentication:
  - Managed Identity: $MANAGED_IDENTITY_ID

Orthanc Credentials:
  - Username: admin
  - Password: $ORTHANC_PASSWORD

Next steps:
  1. Grant DICOM Data Owner role to managed identity (see warning above)
  2. Access Orthanc at: https://$CONTAINER_APP_URL
  3. Test deployment: cd ../../../quickstart/scripts && ./test-deployment.sh --url https://$CONTAINER_APP_URL --password $ORTHANC_PASSWORD
  4. View logs: az containerapp logs show --name orthanc-$ENVIRONMENT_NAME-app --resource-group $RESOURCE_GROUP

EOF

# Save deployment details
cat > deployment-details.json << EOF
{
  "resourceGroup": "$RESOURCE_GROUP",
  "location": "$LOCATION",
  "containerAppUrl": "https://$CONTAINER_APP_URL",
  "postgresFqdn": "$POSTGRES_FQDN",
  "storageAccount": "$STORAGE_ACCOUNT",
  "vnetName": "$VNET_NAME",
  "managedIdentityId": "$MANAGED_IDENTITY_ID",
  "orthancUsername": "admin",
  "orthancPassword": "$ORTHANC_PASSWORD",
  "deploymentName": "$DEPLOYMENT_NAME",
  "deploymentTimestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF

log_info "Deployment details saved to: deployment-details.json"
