# Azure Quickstart Deployment

Deploy Orthanc with OAuth plugin to Azure Container Apps using client credentials authentication.

> 📘 **NEW: Transparent OAuth Integration** - Users can send DICOM studies to Azure using the standard Orthanc UI "Send to DICOMWeb server" button. OAuth authentication happens automatically in the background. See [TRANSPARENT-OAUTH-GUIDE.md](TRANSPARENT-OAUTH-GUIDE.md) for details.

## Overview

This quickstart deploys Orthanc to Azure Container Apps with:
- **Authentication**: OAuth 2.0 client credentials flow (transparent to users)
- **Database**: Azure Database for PostgreSQL Flexible Server
- **Storage**: Azure Blob Storage
- **DICOM Service**: Azure Health Data Services DICOM
- **Networking**: Public endpoints with firewall rules
- **Estimated Cost**: ~$66/month
- **Setup Time**: ~15 minutes

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Azure Subscription                        │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Resource Group: rg-orthanc-quickstart               │  │
│  │                                                       │  │
│  │  ┌─────────────────┐      ┌──────────────────────┐  │  │
│  │  │ Container Apps  │      │ PostgreSQL Flexible  │  │  │
│  │  │   Environment   │      │      Server          │  │  │
│  │  │                 │      │                      │  │  │
│  │  │  ┌───────────┐  │      │  Database: orthanc   │  │  │
│  │  │  │  Orthanc  │──┼──────┤                      │  │  │
│  │  │  │  + OAuth  │  │      └──────────────────────┘  │  │
│  │  │  │  Plugin   │  │                                 │  │
│  │  │  └───────────┘  │      ┌──────────────────────┐  │  │
│  │  │       │         │      │   Blob Storage       │  │  │
│  │  │       │         │      │                      │  │  │
│  │  │       └─────────┼──────┤  Container:          │  │  │
│  │  │                 │      │  orthanc-dicom       │  │  │
│  │  └─────────────────┘      └──────────────────────┘  │  │
│  │                                                       │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Azure Health Data Services                          │  │
│  │  ┌────────────────────────────────────────────────┐  │  │
│  │  │  DICOM Service                                 │  │  │
│  │  │  (OAuth 2.0 protected)                         │  │  │
│  │  └────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Azure AD                                            │  │
│  │  ┌────────────────────────────────────────────────┐  │  │
│  │  │  App Registration (Client Credentials)         │  │  │
│  │  └────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Prerequisites

- **Azure subscription** with Contributor + User Access Administrator roles
- **Azure CLI** 2.50 or later ([Install](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli))
- **Docker** for building custom image ([Install](https://docs.docker.com/get-docker/))
- **jq** for JSON processing ([Install](https://stedolan.github.io/jq/download/))
- **Azure Health Data Services** DICOM workspace already deployed
- **Azure Container Registry** for storing Docker images

## Quick Start

### Step 1: Login to Azure

```bash
az login
az account set --subscription "your-subscription-id"
```

### Step 2: Create App Registration

```bash
cd examples/azure/quickstart
./scripts/setup-app-registration.sh \
  --name "orthanc-quickstart" \
  --dicom-workspace-name "your-dicom-workspace"
```

This creates:
- Azure AD app registration
- Service principal
- Client secret (2-year expiration)
- Outputs credentials to `app-registration.json`

**Important**: Grant admin consent for API permissions:

```bash
APP_ID=$(jq -r '.clientId' app-registration.json)
az ad app permission admin-consent --id $APP_ID
```

### Step 3: Grant DICOM Permissions

Grant the service principal **DICOM Data Owner** role:

```bash
SP_OBJECT_ID=$(jq -r '.servicePrincipalObjectId' app-registration.json)
DICOM_WORKSPACE_ID="/subscriptions/YOUR_SUBSCRIPTION/resourceGroups/YOUR_RG/providers/Microsoft.HealthcareApis/workspaces/YOUR_WORKSPACE"

az role assignment create \
  --assignee $SP_OBJECT_ID \
  --role "DICOM Data Owner" \
  --scope $DICOM_WORKSPACE_ID
```

### Step 4: Configure Parameters

Copy and customize the parameters template:

```bash
cp parameters.json.template parameters.json
```

Edit `parameters.json` and replace:
- `REPLACE_WITH_YOUR_DICOM_SERVICE_URL`
- `REPLACE_WITH_YOUR_TENANT_ID`
- `REPLACE_WITH_YOUR_CLIENT_ID`
- Container registry details

For production, use Key Vault references for secrets instead of plain text.

### Step 5: Deploy

```bash
./scripts/deploy.sh \
  --resource-group rg-orthanc-quickstart \
  --location eastus \
  --registry myregistry
```

This will:
1. Build Docker image with Orthanc + OAuth plugin
2. Push image to Azure Container Registry
3. Deploy Azure resources using Bicep
4. Output deployment details and credentials

Deployment takes ~10-15 minutes.

### Step 6: Test Deployment

```bash
./scripts/test-deployment.sh
```

This validates:
- System status
- OAuth plugin loaded
- Database connectivity
- Metrics endpoint

## Building the Docker Image

**IMPORTANT:** When building for Azure Container Apps, you MUST specify the target platform:

```bash
docker buildx build --platform linux/amd64 -t <registry>/<image>:<tag> -f examples/azure/quickstart/Dockerfile .
```

M1/M2/M3 Macs build arm64 images by default, which will fail on Azure Container Apps (amd64 Linux).

## Cost Estimate

Approximate monthly costs (East US region):

| Resource | SKU | Monthly Cost |
|----------|-----|--------------|
| Container Apps | 1 vCPU, 2GB RAM, ~730 hours | $35 |
| PostgreSQL Flexible | Burstable B2s, 32GB storage | $20 |
| Blob Storage | LRS, ~100GB | $2 |
| Log Analytics | 5GB ingestion | $5 |
| Container Registry | Basic tier | $5 |
| **Total** | | **~$67/month** |

> Costs vary by region and usage. Use [Azure Pricing Calculator](https://azure.microsoft.com/pricing/calculator/) for accurate estimates.

## Configuration

### Environment Variables

The deployment automatically configures:

**Database**:
- `ORTHANC__POSTGRESQL__HOST`
- `ORTHANC__POSTGRESQL__PORT`
- `ORTHANC__POSTGRESQL__DATABASE`
- `ORTHANC__POSTGRESQL__USERNAME`
- `ORTHANC__POSTGRESQL__PASSWORD`

**Storage**:
- `ORTHANC__AZURE_BLOB_STORAGE__CONNECTION_STRING`
- `ORTHANC__AZURE_BLOB_STORAGE__CONTAINER`

**OAuth**:
- `OAUTH_CLIENT_ID`
- `OAUTH_CLIENT_SECRET`
- `OAUTH_TOKEN_ENDPOINT`
- `DICOM_SERVICE_URL`
- `DICOM_SCOPE`

**Orthanc**:
- `ORTHANC_USERNAME`
- `ORTHANC_PASSWORD`

### Scaling

Automatic scaling is configured:
- **Min replicas**: 1
- **Max replicas**: 3
- **Scale trigger**: 50 concurrent requests

Adjust in `main.bicep`:

```bicep
scaleMinReplicas: 1
scaleMaxReplicas: 3
scaleRules: [
  {
    name: 'http-rule'
    http: {
      metadata: {
        concurrentRequests: '50'
      }
    }
  }
]
```

## Accessing Orthanc

### Web Interface

```bash
ORTHANC_URL=$(jq -r '.containerAppUrl' deployment-details.json)
open "https://$ORTHANC_URL"
```

Login with credentials from `deployment-details.json`.

### API Access

```bash
ORTHANC_PASSWORD=$(jq -r '.orthancPassword' deployment-details.json)

curl -u admin:$ORTHANC_PASSWORD https://$ORTHANC_URL/system
```

### Logs

```bash
az containerapp logs show \
  --name orthanc-quickstart-app \
  --resource-group rg-orthanc-quickstart \
  --follow
```

## Monitoring

### Prometheus Metrics

Metrics available at `/metrics` endpoint:

```bash
curl -u admin:$ORTHANC_PASSWORD https://$ORTHANC_URL/metrics
```

Key metrics:
- `orthanc_token_acquisition_total` - OAuth token requests
- `orthanc_token_cache_hits_total` - Token cache hits
- `orthanc_http_requests_total` - HTTP requests to DICOM service

### Log Analytics

View logs in Azure Portal:

```bash
az monitor log-analytics query \
  --workspace $(az containerapp env show --name orthanc-quickstart-cae --resource-group rg-orthanc-quickstart --query properties.appLogsConfiguration.logAnalyticsConfiguration.customerId -o tsv) \
  --analytics-query "ContainerAppConsoleLogs_CL | where ContainerAppName_s == 'orthanc-quickstart-app' | project TimeGenerated, Log_s | order by TimeGenerated desc | take 50"
```

## Troubleshooting

### Container fails to start

**Check logs**:
```bash
az containerapp logs show --name orthanc-quickstart-app --resource-group rg-orthanc-quickstart --tail 100
```

**Common issues**:
- Image pull failure: Check ACR permissions
- Database connection: Verify firewall rules allow Azure services
- Storage connection: Verify connection string is valid

### OAuth authentication fails

**Verify app registration**:
```bash
APP_ID=$(jq -r '.clientId' app-registration.json)
az ad app show --id $APP_ID
```

**Check DICOM permissions**:
```bash
SP_OBJECT_ID=$(jq -r '.servicePrincipalObjectId' app-registration.json)
az role assignment list --assignee $SP_OBJECT_ID --all
```

**Test token acquisition manually**:
```bash
curl -X POST https://login.microsoftonline.com/TENANT_ID/oauth2/v2.0/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=CLIENT_ID&scope=https://dicom.healthcareapis.azure.com/.default&client_secret=CLIENT_SECRET&grant_type=client_credentials"
```

### Database connection errors

**Test connectivity from Container App**:
```bash
az containerapp exec \
  --name orthanc-quickstart-app \
  --resource-group rg-orthanc-quickstart \
  --command /bin/bash

# Inside container
apt-get update && apt-get install -y postgresql-client
psql -h POSTGRES_HOST -U USERNAME -d orthanc
```

## Cleanup

Delete all resources:

```bash
./scripts/cleanup.sh --resource-group rg-orthanc-quickstart
```

Include app registration:

```bash
./scripts/cleanup.sh --resource-group rg-orthanc-quickstart --delete-app-reg --yes
```

## Security Considerations

### Production Checklist

- [ ] Use Azure Key Vault for secrets
- [ ] Enable HTTPS only (configured by default)
- [ ] Implement network restrictions (use production deployment for VNet)
- [ ] Enable Azure Monitor alerts
- [ ] Rotate client secret before 2-year expiration
- [ ] Review and harden database firewall rules
- [ ] Enable diagnostic logging
- [ ] Implement backup strategy for PostgreSQL
- [ ] Configure Azure AD Conditional Access
- [ ] Review RBAC role assignments

### Secrets Management

For production, use Key Vault references:

```json
{
  "oauthClientSecret": {
    "reference": {
      "keyVault": {
        "id": "/subscriptions/.../vaults/my-vault"
      },
      "secretName": "oauth-client-secret"
    }
  }
}
```

## Next Steps

- **Production Deployment**: See [../production/](../production/) for VNet, private endpoints, and managed identity
- **AKS Deployment**: See [../production-aks/](../production-aks/) for Kubernetes with Helm
- **Monitoring**: Configure Application Insights for advanced monitoring
- **Backup**: Set up automated PostgreSQL backups
- **CI/CD**: Implement GitHub Actions workflow for automated deployments

## Support

For issues and questions:
- **Plugin Issues**: [GitHub Issues](https://github.com/rhavekost/orthanc-dicomweb-oauth/issues)
- **Azure Issues**: [Azure Support](https://azure.microsoft.com/support/)
- **Orthanc Questions**: [Orthanc Forum](https://groups.google.com/g/orthanc-users)
