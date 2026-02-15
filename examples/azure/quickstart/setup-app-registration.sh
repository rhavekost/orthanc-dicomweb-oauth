#!/bin/bash
set -e

# ============================================================================
# Azure App Registration Setup Script
# ============================================================================
#
# This script creates an Azure AD app registration with client secret
# for OAuth authentication with Azure Health Data Services DICOM.
#
# Prerequisites:
# - Azure CLI logged in (az login)
# - Sufficient permissions to create app registrations in Azure AD
#
# Output:
# - app-registration.json with clientId, clientSecret, servicePrincipalObjectId
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_FILE="$SCRIPT_DIR/app-registration.json"

echo "============================================================================"
echo "Azure App Registration Setup"
echo "============================================================================"
echo ""

# Check if app-registration.json already exists
if [ -f "$OUTPUT_FILE" ]; then
    echo "⚠ app-registration.json already exists"
    echo ""
    read -p "Do you want to create a NEW app registration? (y/N) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Keeping existing app-registration.json"
        exit 0
    fi
    echo ""
fi

# Check Azure CLI login
if ! az account show &>/dev/null; then
    echo "ERROR: Not logged into Azure CLI"
    echo "Please run: az login"
    exit 1
fi

TENANT_ID=$(az account show --query tenantId -o tsv)
echo "Tenant ID: $TENANT_ID"
echo ""

# ============================================================================
# Create App Registration
# ============================================================================

echo "→ Creating app registration..."

APP_NAME="orthanc-dicom-oauth-$(date +%s)"

# Create app registration
APP_ID=$(az ad app create \
    --display-name "$APP_NAME" \
    --sign-in-audience "AzureADMyOrg" \
    --query appId \
    -o tsv)

if [ -z "$APP_ID" ]; then
    echo "ERROR: Failed to create app registration"
    exit 1
fi

echo "  App ID (Client ID): $APP_ID"

# ============================================================================
# Create Service Principal
# ============================================================================

echo "→ Creating service principal..."

# Create service principal for the app
SP_OBJECT_ID=$(az ad sp create \
    --id "$APP_ID" \
    --query id \
    -o tsv)

if [ -z "$SP_OBJECT_ID" ]; then
    echo "ERROR: Failed to create service principal"
    exit 1
fi

echo "  Service Principal Object ID: $SP_OBJECT_ID"

# ============================================================================
# Create Client Secret
# ============================================================================

echo "→ Creating client secret..."

# Create client secret (valid for 1 year)
CLIENT_SECRET=$(az ad app credential reset \
    --id "$APP_ID" \
    --append \
    --display-name "quickstart-secret" \
    --years 1 \
    --query password \
    -o tsv)

if [ -z "$CLIENT_SECRET" ]; then
    echo "ERROR: Failed to create client secret"
    exit 1
fi

echo "  Client Secret: [hidden]"
echo "  ⚠ Secret will expire in 1 year"

# ============================================================================
# Save to file
# ============================================================================

echo ""
echo "→ Saving configuration..."

cat > "$OUTPUT_FILE" <<EOF
{
  "tenantId": "$TENANT_ID",
  "clientId": "$APP_ID",
  "clientSecret": "$CLIENT_SECRET",
  "servicePrincipalObjectId": "$SP_OBJECT_ID",
  "displayName": "$APP_NAME",
  "createdAt": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF

echo "✓ Configuration saved to: $OUTPUT_FILE"
echo ""

# ============================================================================
# Display summary
# ============================================================================

echo "============================================================================"
echo "APP REGISTRATION CREATED SUCCESSFULLY"
echo "============================================================================"
echo ""
echo "Application Details:"
echo "  Display Name: $APP_NAME"
echo "  Tenant ID: $TENANT_ID"
echo "  Client ID: $APP_ID"
echo "  Service Principal Object ID: $SP_OBJECT_ID"
echo ""
echo "Security:"
echo "  ⚠ Client secret saved to app-registration.json"
echo "  ⚠ Keep this file secure - it contains sensitive credentials"
echo "  ⚠ Secret expires: $(date -u -v+1y +%Y-%m-%d 2>/dev/null || date -u -d '+1 year' +%Y-%m-%d 2>/dev/null || echo '1 year from now')"
echo "  ⚠ Add app-registration.json to .gitignore"
echo ""
echo "Next Steps:"
echo "  1. Review the app registration in Azure Portal:"
echo "     https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationMenuBlade/~/Overview/appId/$APP_ID"
echo "  2. Run the deployment script: ./deploy.sh"
echo ""
echo "Note:"
echo "  DICOM Data Owner permissions will be assigned during deployment"
echo ""
echo "============================================================================"
