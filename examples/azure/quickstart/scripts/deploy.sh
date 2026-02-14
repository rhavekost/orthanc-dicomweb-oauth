#!/usr/bin/env bash
set -euo pipefail

# ========================================
# Deploy Orthanc OAuth Quickstart to Azure
# ========================================
#
# This script deploys the Orthanc OAuth plugin quickstart to Azure using Bicep.
#
# Prerequisites:
# - Azure CLI 2.50+
# - Docker (for building custom image)
# - App registration created (run setup-app-registration.sh first)
# - Azure Container Registry
#
# Usage:
#   ./deploy.sh --resource-group rg-orthanc-demo --location eastus
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
ENVIRONMENT_NAME="quickstart"
PARAMETERS_FILE="parameters.json"
APP_REG_FILE="app-registration.json"
BUILD_IMAGE=true
CONTAINER_REGISTRY=""
IMAGE_TAG="latest"

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

Deploy Orthanc OAuth quickstart to Azure Container Apps.

OPTIONS:
    -g, --resource-group NAME    Resource group name (required)
    -l, --location LOCATION      Azure region (default: eastus)
    -e, --environment NAME       Environment name (default: quickstart)
    -p, --parameters FILE        Parameters JSON file (default: parameters.json)
    -a, --app-reg FILE           App registration JSON file (default: app-registration.json)
    -r, --registry NAME          Azure Container Registry name (required if building image)
    -t, --tag TAG                Container image tag (default: latest)
    --no-build                   Skip building container image
    -h, --help                   Show this help message

EXAMPLE:
    $0 --resource-group rg-orthanc-demo --location eastus --registry myregistry

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
        -a|--app-reg)
            APP_REG_FILE="$2"
            shift 2
            ;;
        -r|--registry)
            CONTAINER_REGISTRY="$2"
            shift 2
            ;;
        -t|--tag)
            IMAGE_TAG="$2"
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

# ========================================
# Main Script
# ========================================

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

log_step "Step 1/6: Validating prerequisites"

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

# Check app registration file
if [[ ! -f "$APP_REG_FILE" ]]; then
    log_error "App registration file not found: $APP_REG_FILE"
    log_error "Run setup-app-registration.sh first"
    exit 1
fi

# Load app registration details
CLIENT_ID=$(jq -r '.clientId' "$APP_REG_FILE")
CLIENT_SECRET=$(jq -r '.clientSecret' "$APP_REG_FILE")
TENANT_ID=$(jq -r '.tenantId' "$APP_REG_FILE")
TOKEN_ENDPOINT=$(jq -r '.tokenEndpoint' "$APP_REG_FILE")
DICOM_SCOPE=$(jq -r '.dicomScope' "$APP_REG_FILE")

log_info "Using app registration: $CLIENT_ID"

# ========================================
# Build and Push Container Image
# ========================================

if [[ "$BUILD_IMAGE" == true ]]; then
    log_step "Step 2/6: Building and pushing container image"

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
    log_step "Step 2/6: Skipping image build (--no-build specified)"

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

log_step "Step 3/6: Creating resource group"

if az group show --name "$RESOURCE_GROUP" &> /dev/null; then
    log_info "Resource group already exists: $RESOURCE_GROUP"
else
    log_info "Creating resource group: $RESOURCE_GROUP"
    az group create --name "$RESOURCE_GROUP" --location "$LOCATION"
fi

# ========================================
# Generate Deployment Parameters
# ========================================

log_step "Step 4/6: Generating deployment parameters"

# Read DICOM service URL from parameters file
DICOM_SERVICE_URL=$(jq -r '.parameters.dicomServiceUrl.value' "$PARAMETERS_FILE")

# Reuse existing passwords if deployment-details.json exists (idempotency)
if [[ -f "deployment-details.json" ]]; then
    log_info "Found existing deployment - reusing credentials"
    POSTGRES_PASSWORD=$(jq -r '.postgresPassword // empty' deployment-details.json)
    ORTHANC_PASSWORD=$(jq -r '.orthancPassword' deployment-details.json)
fi

# Generate secure passwords only if not found
if [[ -z "$POSTGRES_PASSWORD" ]]; then
    log_info "Generating new PostgreSQL password"
    POSTGRES_PASSWORD=$(openssl rand -base64 32)
else
    log_info "Reusing existing PostgreSQL password"
fi

if [[ -z "$ORTHANC_PASSWORD" ]]; then
    log_info "Generating new Orthanc password"
    ORTHANC_PASSWORD=$(openssl rand -base64 24)
else
    log_info "Reusing existing Orthanc password"
fi

# Create deployment parameters
cat > deployment-params.json << EOF
{
  "environmentName": "$ENVIRONMENT_NAME",
  "location": "$LOCATION",
  "resourceGroupName": "$RESOURCE_GROUP",
  "containerImage": "$CONTAINER_IMAGE",
  "containerRegistryName": "$CONTAINER_REGISTRY",
  "dicomServiceUrl": "$DICOM_SERVICE_URL",
  "tenantId": "$TENANT_ID",
  "dicomScope": "$DICOM_SCOPE",
  "oauthClientId": "$CLIENT_ID",
  "oauthClientSecret": "$CLIENT_SECRET",
  "postgresAdminUsername": "orthanc_admin",
  "postgresAdminPassword": "$POSTGRES_PASSWORD",
  "orthancUsername": "admin",
  "orthancPassword": "$ORTHANC_PASSWORD"
}
EOF

log_info "Deployment parameters generated"

# ========================================
# Deploy Bicep Template
# ========================================

log_step "Step 5/6: Deploying Azure resources with Bicep"

DEPLOYMENT_NAME="orthanc-quickstart-$(date +%Y%m%d-%H%M%S)"

log_info "Starting deployment: $DEPLOYMENT_NAME"

az deployment sub create \
    --name "$DEPLOYMENT_NAME" \
    --location "$LOCATION" \
    --template-file "$SCRIPT_DIR/../main.bicep" \
    --parameters @deployment-params.json \
    --output json > deployment-output.json

log_info "Deployment complete"

# ========================================
# Display Outputs
# ========================================

log_step "Step 6/6: Deployment summary"

CONTAINER_APP_URL=$(jq -r '.properties.outputs.containerAppUrl.value' deployment-output.json)
POSTGRES_FQDN=$(jq -r '.properties.outputs.postgresServerFqdn.value' deployment-output.json)
STORAGE_ACCOUNT=$(jq -r '.properties.outputs.storageAccountName.value' deployment-output.json)

cat << EOF

${GREEN}✓ Deployment successful!${NC}

Resource Group: $RESOURCE_GROUP
Location: $LOCATION

Resources deployed:
  - Container App: https://$CONTAINER_APP_URL
  - PostgreSQL: $POSTGRES_FQDN
  - Storage Account: $STORAGE_ACCOUNT

Orthanc Credentials:
  - Username: admin
  - Password: $ORTHANC_PASSWORD

Next steps:
  1. Access Orthanc at: https://$CONTAINER_APP_URL
  2. Test DICOM upload: ./scripts/test-deployment.sh
  3. View logs: az containerapp logs show --name orthanc-$ENVIRONMENT_NAME-app --resource-group $RESOURCE_GROUP

EOF

# Save deployment details
cat > deployment-details.json << EOF
{
  "resourceGroup": "$RESOURCE_GROUP",
  "location": "$LOCATION",
  "containerAppUrl": "https://$CONTAINER_APP_URL",
  "postgresFqdn": "$POSTGRES_FQDN",
  "storageAccount": "$STORAGE_ACCOUNT",
  "orthancUsername": "admin",
  "orthancPassword": "$ORTHANC_PASSWORD",
  "postgresPassword": "$POSTGRES_PASSWORD",
  "deploymentName": "$DEPLOYMENT_NAME",
  "deploymentTimestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF

log_info "Deployment details saved to: deployment-details.json"
