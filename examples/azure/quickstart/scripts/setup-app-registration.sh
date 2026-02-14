#!/usr/bin/env bash
set -euo pipefail

# ========================================
# Setup Azure AD App Registration
# ========================================
#
# This script creates an Azure AD app registration and service principal
# for OAuth client credentials authentication with Azure Health Data Services.
#
# Prerequisites:
# - Azure CLI 2.50+
# - User with Application Administrator or Global Administrator role
#
# Usage:
#   ./setup-app-registration.sh --name "orthanc-quickstart" --dicom-workspace-name "my-workspace"
#

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
APP_NAME=""
DICOM_WORKSPACE_NAME=""
OUTPUT_FILE="app-registration.json"

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

show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Create Azure AD app registration for Orthanc OAuth plugin.

OPTIONS:
    -n, --name NAME                  App registration name (required)
    -w, --dicom-workspace-name NAME  DICOM workspace name (required)
    -o, --output FILE                Output JSON file (default: app-registration.json)
    -h, --help                       Show this help message

EXAMPLE:
    $0 --name "orthanc-quickstart" --dicom-workspace-name "my-workspace"

EOF
}

# ========================================
# Parse Arguments
# ========================================

while [[ $# -gt 0 ]]; do
    case $1 in
        -n|--name)
            APP_NAME="$2"
            shift 2
            ;;
        -w|--dicom-workspace-name)
            DICOM_WORKSPACE_NAME="$2"
            shift 2
            ;;
        -o|--output)
            OUTPUT_FILE="$2"
            shift 2
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
if [[ -z "$APP_NAME" ]]; then
    log_error "App name is required"
    show_usage
    exit 1
fi

if [[ -z "$DICOM_WORKSPACE_NAME" ]]; then
    log_error "DICOM workspace name is required"
    show_usage
    exit 1
fi

# ========================================
# Main Script
# ========================================

log_info "Creating app registration: $APP_NAME"

# Check Azure CLI version
az version --output tsv > /dev/null 2>&1 || {
    log_error "Azure CLI not found. Please install Azure CLI 2.50+"
    exit 1
}

# Check logged in
az account show > /dev/null 2>&1 || {
    log_error "Not logged in to Azure. Run 'az login' first."
    exit 1
}

TENANT_ID=$(az account show --query tenantId -o tsv)
log_info "Using tenant: $TENANT_ID"

# Create app registration
log_info "Creating Azure AD application..."
APP_ID=$(az ad app create \
    --display-name "$APP_NAME" \
    --sign-in-audience AzureADMyOrg \
    --query appId -o tsv)

log_info "App ID: $APP_ID"

# Create service principal
log_info "Creating service principal..."
SP_OBJECT_ID=$(az ad sp create \
    --id "$APP_ID" \
    --query id -o tsv)

log_info "Service Principal Object ID: $SP_OBJECT_ID"

# Create client secret
log_info "Creating client secret..."
CLIENT_SECRET=$(az ad app credential reset \
    --id "$APP_ID" \
    --append \
    --years 2 \
    --query password -o tsv)

# Get DICOM service scope
DICOM_SCOPE="https://dicom.healthcareapis.azure.com/.default"
log_info "DICOM API scope: $DICOM_SCOPE"

# Grant API permissions
log_info "Granting API permissions for DICOM service..."
DICOM_API_ID="4f6778d8-5aef-43dc-a1ff-b073724ed0a4"  # Azure Healthcare APIs
DICOM_PERMISSION_ID="4c0bc8c2-3e8d-4d5e-8a4e-05e1be780e15"  # user_impersonation

az ad app permission add \
    --id "$APP_ID" \
    --api "$DICOM_API_ID" \
    --api-permissions "${DICOM_PERMISSION_ID}=Scope"

log_warn "Admin consent is required for the API permissions."
log_warn "Grant admin consent in the Azure Portal or run:"
log_warn "  az ad app permission admin-consent --id $APP_ID"

# Save output
cat > "$OUTPUT_FILE" << EOF
{
  "appName": "$APP_NAME",
  "tenantId": "$TENANT_ID",
  "clientId": "$APP_ID",
  "clientSecret": "$CLIENT_SECRET",
  "servicePrincipalObjectId": "$SP_OBJECT_ID",
  "dicomScope": "$DICOM_SCOPE",
  "tokenEndpoint": "https://login.microsoftonline.com/$TENANT_ID/oauth2/v2.0/token"
}
EOF

log_info "App registration details saved to: $OUTPUT_FILE"
log_info ""
log_info "Next steps:"
log_info "1. Grant admin consent for API permissions:"
log_info "   az ad app permission admin-consent --id $APP_ID"
log_info ""
log_info "2. Grant DICOM Data Owner role to the service principal:"
log_info "   az role assignment create \\"
log_info "     --assignee $SP_OBJECT_ID \\"
log_info "     --role 'DICOM Data Owner' \\"
log_info "     --scope /subscriptions/SUBSCRIPTION_ID/resourceGroups/RG_NAME/providers/Microsoft.HealthcareApis/workspaces/$DICOM_WORKSPACE_NAME"
log_info ""
log_info "${GREEN}App registration created successfully!${NC}"
