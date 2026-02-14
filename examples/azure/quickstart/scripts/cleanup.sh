#!/usr/bin/env bash
set -euo pipefail

# ========================================
# Cleanup Azure Resources
# ========================================
#
# This script safely removes all Azure resources created by the deployment.
#
# Prerequisites:
# - Azure CLI 2.50+
# - Appropriate permissions to delete resources
#
# Usage:
#   ./cleanup.sh --resource-group rg-orthanc-demo
#

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
RESOURCE_GROUP=""
DELETE_APP_REG=false
SKIP_CONFIRMATION=false
APP_REG_FILE="app-registration.json"

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

Delete Azure resources created by Orthanc deployment.

OPTIONS:
    -g, --resource-group NAME    Resource group name (required)
    -a, --delete-app-reg         Also delete app registration
    -f, --app-reg-file FILE      App registration JSON (default: app-registration.json)
    -y, --yes                    Skip confirmation prompt
    -h, --help                   Show this help message

EXAMPLE:
    $0 --resource-group rg-orthanc-demo
    $0 --resource-group rg-orthanc-demo --delete-app-reg --yes

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
        -a|--delete-app-reg)
            DELETE_APP_REG=true
            shift
            ;;
        -f|--app-reg-file)
            APP_REG_FILE="$2"
            shift 2
            ;;
        -y|--yes)
            SKIP_CONFIRMATION=true
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

# ========================================
# Main Script
# ========================================

log_warn "This will delete the following resources:"
echo "  - Resource group: $RESOURCE_GROUP"
echo "  - All resources within the resource group"

if [[ "$DELETE_APP_REG" == true ]]; then
    if [[ -f "$APP_REG_FILE" ]]; then
        APP_ID=$(jq -r '.clientId' "$APP_REG_FILE")
        echo "  - App registration: $APP_ID"
    else
        log_warn "App registration file not found: $APP_REG_FILE"
    fi
fi

echo ""

if [[ "$SKIP_CONFIRMATION" != true ]]; then
    read -p "Are you sure you want to continue? (type 'yes' to confirm): " CONFIRM
    if [[ "$CONFIRM" != "yes" ]]; then
        log_info "Cleanup cancelled"
        exit 0
    fi
fi

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

# ========================================
# Delete Resource Group
# ========================================

log_info "Deleting resource group: $RESOURCE_GROUP"

if az group show --name "$RESOURCE_GROUP" &> /dev/null; then
    az group delete --name "$RESOURCE_GROUP" --yes --no-wait
    log_info "Resource group deletion initiated (running in background)"
else
    log_warn "Resource group not found: $RESOURCE_GROUP"
fi

# ========================================
# Delete App Registration
# ========================================

if [[ "$DELETE_APP_REG" == true && -f "$APP_REG_FILE" ]]; then
    log_info "Deleting app registration"

    APP_ID=$(jq -r '.clientId' "$APP_REG_FILE")

    if az ad app show --id "$APP_ID" &> /dev/null; then
        az ad app delete --id "$APP_ID"
        log_info "App registration deleted: $APP_ID"
    else
        log_warn "App registration not found: $APP_ID"
    fi
fi

# ========================================
# Summary
# ========================================

cat << EOF

${GREEN}✓ Cleanup initiated${NC}

Resources are being deleted in the background.
You can check status with:

  az group show --name $RESOURCE_GROUP

To monitor deletion progress:

  az group wait --name $RESOURCE_GROUP --deleted

EOF
