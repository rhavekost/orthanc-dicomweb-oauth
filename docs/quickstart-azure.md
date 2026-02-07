# Quick Start: Azure Health Data Services

This guide shows how to connect Orthanc to Azure Health Data Services DICOM service using OAuth2.

## Prerequisites

- Azure subscription
- Azure Health Data Services workspace with DICOM service
- Service principal (app registration) with DICOM access

## Step 1: Create Service Principal

```bash
# Create app registration
az ad app create --display-name "orthanc-dicomweb-client"

# Get application ID
APP_ID=$(az ad app list --display-name "orthanc-dicomweb-client" --query "[0].appId" -o tsv)

# Create service principal
az ad sp create --id $APP_ID

# Create client secret
az ad app credential reset --id $APP_ID --append
```

Save the `appId` (client ID) and `password` (client secret).

## Step 2: Grant DICOM Access

```bash
# Get DICOM service details
DICOM_URL="https://workspace-dicom.dicom.azurehealthcareapis.com"
RESOURCE_GROUP="your-resource-group"
WORKSPACE_NAME="your-workspace"
DICOM_SERVICE_NAME="your-dicom-service"

# Get service principal object ID
SP_OBJECT_ID=$(az ad sp show --id $APP_ID --query id -o tsv)

# Assign DICOM Data Owner role
az role assignment create \
  --role "DICOM Data Owner" \
  --assignee $SP_OBJECT_ID \
  --scope "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.HealthcareApis/workspaces/$WORKSPACE_NAME/dicomservices/$DICOM_SERVICE_NAME"
```

## Step 3: Configure Orthanc

Add to `orthanc.json`:

```json
{
  "Plugins": [
    "/etc/orthanc/plugins/dicomweb_oauth_plugin.py"
  ],

  "DicomWebOAuth": {
    "Servers": {
      "azure-dicom": {
        "Url": "https://workspace-dicom.dicom.azurehealthcareapis.com/v2/",
        "TokenEndpoint": "https://login.microsoftonline.com/{tenant-id}/oauth2/v2.0/token",
        "ClientId": "${AZURE_CLIENT_ID}",
        "ClientSecret": "${AZURE_CLIENT_SECRET}",
        "Scope": "https://dicom.healthcareapis.azure.com/.default",
        "TokenRefreshBufferSeconds": 300
      }
    }
  }
}
```

Replace `{tenant-id}` with your Azure AD tenant ID.

## Step 4: Set Environment Variables

```bash
export AZURE_CLIENT_ID="your-app-id"
export AZURE_CLIENT_SECRET="your-client-secret"
```

Or create `.env` file:
```
AZURE_CLIENT_ID=your-app-id
AZURE_CLIENT_SECRET=your-client-secret
```

## Step 5: Test Connection

```bash
# Check plugin status
curl http://localhost:8042/dicomweb-oauth/status

# Test token acquisition
curl -X POST http://localhost:8042/dicomweb-oauth/servers/azure-dicom/test

# Query DICOM studies
curl http://localhost:8042/dicom-web/studies
```

## Troubleshooting

### Error: "invalid_client"

- Verify client ID and secret are correct
- Check service principal was created
- Ensure credentials are not expired

### Error: "insufficient_claims"

- Verify DICOM Data Owner role is assigned
- Check role assignment scope matches your DICOM service
- Wait 5-10 minutes for role propagation

### Error: "resource not found"

- Verify DICOM service URL is correct
- Ensure URL ends with `/v2/`
- Check workspace and service names

## Azure-Specific Notes

- **Tenant ID**: Find in Azure Portal → Azure Active Directory → Overview
- **Scope**: Always use `https://dicom.healthcareapis.azure.com/.default`
- **Token Lifetime**: Azure AD tokens typically valid for 1 hour
- **Rate Limits**: Azure Health Data Services has API rate limits

## Security Best Practices

1. **Use Managed Identity** in production (Azure VM/Container Apps)
2. **Rotate secrets** regularly (90-day maximum)
3. **Use Key Vault** for secret storage
4. **Apply least privilege** - use DICOM Data Reader if read-only access needed
5. **Monitor access** via Azure Monitor and Log Analytics

## References

- [Azure Health Data Services](https://docs.microsoft.com/azure/healthcare-apis/)
- [Azure AD OAuth 2.0](https://docs.microsoft.com/azure/active-directory/develop/v2-oauth2-client-creds-grant-flow)
- [DICOM service roles](https://docs.microsoft.com/azure/healthcare-apis/dicom/dicom-services-authorization)
