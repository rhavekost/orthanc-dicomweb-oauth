#!/usr/bin/env bash
set -euo pipefail

# ========================================
# Grant DICOM Permissions to Managed Identity
# ========================================
#
# This script grants DICOM Data Owner role to the Container App's
# managed identity for accessing Azure Health Data Services.
#
# Prerequisites:
# - Azure CLI 2.50+
# - Deployment completed (deployment-details.json exists)
# - User with permissions to assign roles on DICOM service
#
# Usage:
#   ./grant-dicom-permissions.sh --dicom-workspace-id /subscriptions/.../workspaces/my-workspace
#

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
DICOM_WORKSPACE_ID=""
DEPLOYMENT_DETAILS_FILE="deployment-details.json"

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

Grant DICOM Data Owner role to Container App managed identity.

OPTIONS:
    -w, --dicom-workspace-id ID     DICOM workspace resource ID (required)
    -d, --deployment FILE           Deployment details JSON (default: deployment-details.json)
    -h, --help                      Show this help message

EXAMPLE:
    $0 --dicom-workspace-id /subscriptions/abc123/resourceGroups/rg-dicom/providers/Microsoft.HealthcareApis/workspaces/my-workspace

EOF
}

# ========================================
# Parse Arguments
# ========================================

while [[ $# -gt 0 ]]; do
    case $1 in
        -w|--dicom-workspace-id)
            DICOM_WORKSPACE_ID="$2"
            shift 2
            ;;
        -d|--deployment)
            DEPLOYMENT_DETAILS_FILE="$2"
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
if [[ -z "$DICOM_WORKSPACE_ID" ]]; then
    log_error "DICOM workspace ID is required"
    show_usage
    exit 1
fi

# ========================================
# Main Script
# ========================================

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

# Check deployment details file exists
if [[ ! -f "$DEPLOYMENT_DETAILS_FILE" ]]; then
    log_error "Deployment details file not found: $DEPLOYMENT_DETAILS_FILE"
    log_error "Run deploy.sh first"
    exit 1
fi

# Load managed identity ID from deployment details
MANAGED_IDENTITY_ID=$(jq -r '.managedIdentityId' "$DEPLOYMENT_DETAILS_FILE")

if [[ -z "$MANAGED_IDENTITY_ID" || "$MANAGED_IDENTITY_ID" == "null" ]]; then
    log_error "Could not find managed identity ID in deployment details"
    exit 1
fi

log_info "Managed Identity: $MANAGED_IDENTITY_ID"
log_info "DICOM Workspace: $DICOM_WORKSPACE_ID"

# Grant DICOM Data Owner role
log_info "Granting DICOM Data Owner role..."

az role assignment create \
    --assignee "$MANAGED_IDENTITY_ID" \
    --role "DICOM Data Owner" \
    --scope "$DICOM_WORKSPACE_ID"

log_info "${GREEN}✓ DICOM permissions granted successfully!${NC}"

# Verify role assignment
log_info "Verifying role assignment..."

ROLE_ASSIGNMENTS=$(az role assignment list \
    --assignee "$MANAGED_IDENTITY_ID" \
    --scope "$DICOM_WORKSPACE_ID" \
    --query "[?roleDefinitionName=='DICOM Data Owner'].roleDefinitionName" \
    -o tsv)

if [[ "$ROLE_ASSIGNMENTS" == "DICOM Data Owner" ]]; then
    log_info "${GREEN}✓ Verification successful - Role assignment confirmed${NC}"
else
    log_warn "Could not verify role assignment. Check Azure Portal."
fi

cat << EOF

${GREEN}✓ Configuration complete!${NC}

The Container App can now access the DICOM service using its managed identity.

Next steps:
  1. Test DICOM connectivity
  2. Upload test images to verify OAuth authentication
  3. Monitor Container App logs for any authentication errors

EOF
