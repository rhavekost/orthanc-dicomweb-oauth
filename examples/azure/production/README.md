# Azure Production Deployment

Deploy Orthanc with OAuth plugin to Azure Container Apps using **managed identity**, **private networking**, and **VNet integration**.

## Overview

This production deployment provides:
- **Authentication**: Managed Identity (no client secrets)
- **Networking**: Private VNet with isolated subnets
- **Database**: Azure Database for PostgreSQL Flexible Server (private endpoint)
- **Storage**: Azure Blob Storage (private endpoint)
- **DICOM Service**: Azure Health Data Services DICOM
- **Security**: Network isolation, NSGs, Private DNS
- **High Availability**: Auto-scaling (2-10 replicas), zone redundancy
- **Estimated Cost**: ~$350/month
- **Setup Time**: ~30 minutes

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Azure Subscription                          │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Virtual Network (10.0.0.0/16)                            │ │
│  │                                                             │ │
│  │  ┌──────────────────────────────────────────────────────┐ │ │
│  │  │  Subnet: Container Apps (10.0.1.0/24)               │ │ │
│  │  │  Delegation: Microsoft.App/environments              │ │ │
│  │  │                                                       │ │ │
│  │  │  ┌────────────────────────────────────────────────┐ │ │ │
│  │  │  │  Container Apps Environment                    │ │ │ │
│  │  │  │  ┌──────────────────────────────────────────┐ │ │ │ │
│  │  │  │  │  Orthanc + OAuth (Managed Identity)      │ │ │ │ │
│  │  │  │  │  - System-assigned identity               │ │ │ │ │
│  │  │  │  │  - Auto-scaling: 2-10 replicas           │ │ │ │ │
│  │  │  │  └──────────────────────────────────────────┘ │ │ │ │
│  │  │  └────────────────────────────────────────────────┘ │ │ │
│  │  └──────────────────────────────────────────────────────┘ │ │
│  │                                                             │ │
│  │  ┌──────────────────────────────────────────────────────┐ │ │
│  │  │  Subnet: Private Endpoints (10.0.2.0/24)            │ │ │
│  │  │                                                       │ │ │
│  │  │  ┌───────────────┐    ┌──────────────────────────┐ │ │ │
│  │  │  │  PostgreSQL   │    │  Blob Storage            │ │ │ │
│  │  │  │  Private      │    │  Private Endpoint        │ │ │ │
│  │  │  │  Endpoint     │    │                          │ │ │ │
│  │  │  └───────────────┘    └──────────────────────────┘ │ │ │
│  │  └──────────────────────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Private DNS Zones                                         │ │
│  │  - privatelink.postgres.database.azure.com                 │ │
│  │  - privatelink.blob.core.windows.net                       │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Azure Health Data Services                                │ │
│  │  ┌──────────────────────────────────────────────────────┐ │ │
│  │  │  DICOM Service (Managed Identity authentication)      │ │ │
│  │  └──────────────────────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Key Differences from Quickstart

| Feature | Quickstart | Production |
|---------|-----------|------------|
| Authentication | Client ID + Secret | Managed Identity |
| Networking | Public endpoints | Private VNet |
| Database Access | Public with firewall | Private endpoint |
| Storage Access | Public with firewall | Private endpoint |
| Isolation | Basic | Network-level isolation |
| Scaling | 1-3 replicas | 2-10 replicas |
| Cost | ~$67/month | ~$350/month |
| Security | Good | Enhanced |

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

### Step 2: Configure Parameters

```bash
cd examples/azure/production
cp parameters.json.template parameters.json
```

Edit `parameters.json` and replace:
- `REPLACE_WITH_YOUR_DICOM_SERVICE_URL`
- `REPLACE_WITH_YOUR_REGISTRY_NAME`
- `REPLACE_WITH_ACR_RESOURCE_GROUP`
- VNet address prefixes (if needed)

### Step 3: Deploy Infrastructure

```bash
./scripts/deploy.sh \
  --resource-group rg-orthanc-production \
  --location eastus \
  --registry myregistry \
  --registry-rg rg-shared-services
```

This will:
1. Build Docker image with Orthanc + OAuth plugin
2. Push image to Azure Container Registry
3. Deploy VNet with subnets and NSGs
4. Deploy PostgreSQL with private endpoint
5. Deploy Storage Account with private endpoint
6. Deploy Container Apps Environment (VNet-integrated)
7. Deploy Container App with managed identity
8. Configure role assignments for ACR and Storage

Deployment takes ~25-30 minutes.

### Step 4: Grant DICOM Permissions

```bash
./scripts/grant-dicom-permissions.sh \
  --dicom-workspace-id "/subscriptions/YOUR_SUB/resourceGroups/YOUR_RG/providers/Microsoft.HealthcareApis/workspaces/YOUR_WORKSPACE"
```

This grants the managed identity **DICOM Data Owner** role.

### Step 5: Test Deployment

```bash
cd ../../quickstart/scripts
./test-deployment.sh --url https://orthanc-production-app.example.com --password YOUR_PASSWORD
```

## Cost Estimate

Approximate monthly costs (East US region):

| Resource | SKU | Monthly Cost |
|----------|-----|--------------|
| Container Apps | Dedicated, 2-10 vCPU, 4-20GB RAM | $150 |
| PostgreSQL Flexible | GeneralPurpose D2ds_v4, 128GB storage | $120 |
| VNet | Standard tier with private endpoints | $15 |
| Private Endpoints | 2 endpoints | $20 |
| Blob Storage | LRS, ~100GB | $2 |
| Log Analytics | 10GB ingestion | $10 |
| Container Registry | Standard tier | $20 |
| Private DNS Zones | 2 zones | $2 |
| **Total** | | **~$339/month** |

> Costs vary by region, usage, and scaling. Use [Azure Pricing Calculator](https://azure.microsoft.com/pricing/calculator/) for accurate estimates.

## Configuration

### Managed Identity

The Container App uses a **system-assigned managed identity** for authentication:
- No client secrets to manage or rotate
- Automatic credential management by Azure
- Role assignments:
  - **ACR Pull** - Pull container images
  - **Storage Blob Data Contributor** - Access DICOM files
  - **DICOM Data Owner** - Access DICOM service

### Network Isolation

The deployment creates:
- **VNet** with two subnets:
  - Container Apps subnet (delegated)
  - Private Endpoints subnet
- **Network Security Groups** with rules:
  - Allow HTTPS inbound (443)
  - Allow VNet-to-VNet traffic
  - Deny all other inbound traffic
- **Private Endpoints** for:
  - PostgreSQL Flexible Server
  - Blob Storage
- **Private DNS Zones** for name resolution:
  - `privatelink.postgres.database.azure.com`
  - `privatelink.blob.core.windows.net`

### Scaling

Production deployment includes enhanced auto-scaling:
- **Min replicas**: 2 (high availability)
- **Max replicas**: 10 (handle traffic spikes)
- **Scale triggers**:
  - HTTP concurrent requests (50 threshold)
  - CPU utilization (75% threshold)

Adjust in `main.bicep`:

```bicep
scaleMinReplicas: 2
scaleMaxReplicas: 10
scaleRules: [
  {
    name: 'http-rule'
    http: {
      metadata: {
        concurrentRequests: '50'
      }
    }
  }
  {
    name: 'cpu-rule'
    custom: {
      type: 'cpu'
      metadata: {
        type: 'Utilization'
        value: '75'
      }
    }
  }
]
```

## Accessing Orthanc

### From Within VNet

If accessing from resources within the VNet:

```bash
ORTHANC_URL=$(jq -r '.containerAppUrl' deployment-details.json)
curl -u admin:PASSWORD https://$ORTHANC_URL/system
```

### From Internet

For internal-only deployments (`enableNetworkIsolation: true`), you need:
- Azure Bastion or VPN connection to VNet
- Or deploy Application Gateway with public IP

For external access, set in `main.bicepparam`:
```bicep
param enableNetworkIsolation = false  // Allows external ingress
```

### Logs

```bash
az containerapp logs show \
  --name orthanc-production-app \
  --resource-group rg-orthanc-production \
  --follow
```

## Monitoring

### Prometheus Metrics

Metrics available at `/metrics` endpoint:

```bash
curl -u admin:PASSWORD https://$ORTHANC_URL/metrics
```

Key metrics:
- `orthanc_managed_identity_token_acquisition_total` - Managed identity token requests
- `orthanc_token_cache_hits_total` - Token cache hits
- `orthanc_http_requests_total` - HTTP requests to DICOM service

### Log Analytics

Query logs in Azure Portal or CLI:

```bash
WORKSPACE_ID=$(az containerapp env show \
  --name orthanc-production-cae \
  --resource-group rg-orthanc-production \
  --query properties.appLogsConfiguration.logAnalyticsConfiguration.customerId -o tsv)

az monitor log-analytics query \
  --workspace $WORKSPACE_ID \
  --analytics-query "ContainerAppConsoleLogs_CL | where TimeGenerated > ago(1h) | project TimeGenerated, Log_s | order by TimeGenerated desc"
```

## Troubleshooting

### Managed Identity Authentication Fails

**Check role assignments**:
```bash
IDENTITY_ID=$(jq -r '.managedIdentityId' deployment-details.json)
az role assignment list --assignee $IDENTITY_ID --all
```

**Expected roles**:
- ACR Pull (on Container Registry)
- Storage Blob Data Contributor (on Storage Account)
- DICOM Data Owner (on DICOM workspace)

**Test managed identity token**:
```bash
az containerapp exec \
  --name orthanc-production-app \
  --resource-group rg-orthanc-production \
  --command /bin/bash

# Inside container
curl -H "Metadata: true" "http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource=https://dicom.healthcareapis.azure.com"
```

### Private Endpoint Resolution Issues

**Check Private DNS zones are linked to VNet**:
```bash
az network private-dns link vnet list \
  --resource-group rg-orthanc-production \
  --zone-name privatelink.postgres.database.azure.com
```

**Test DNS resolution from Container App**:
```bash
az containerapp exec \
  --name orthanc-production-app \
  --resource-group rg-orthanc-production \
  --command /bin/bash

# Inside container
apt-get update && apt-get install -y dnsutils
nslookup orthanc-production-db-xxx.postgres.database.azure.com
```

Should resolve to private IP (10.0.2.x).

### Database Connection Errors

**Check NSG rules allow VNet traffic**:
```bash
az network nsg rule list \
  --resource-group rg-orthanc-production \
  --nsg-name orthanc-production-nsg-privateEndpoints \
  --query "[].{Name:name, Priority:priority, Direction:direction, Access:access}"
```

**Test connectivity from Container App**:
```bash
az containerapp exec \
  --name orthanc-production-app \
  --resource-group rg-orthanc-production \
  --command /bin/bash

# Inside container
apt-get update && apt-get install -y postgresql-client
psql -h POSTGRES_HOST -U orthanc_admin -d orthanc
```

## Cleanup

Delete all resources:

```bash
cd ../../quickstart/scripts
./cleanup.sh --resource-group rg-orthanc-production --yes
```

**Note**: This deletes the entire resource group including VNet, private endpoints, and all data.

## Security Considerations

### Production Checklist

- [x] Use Managed Identity (no client secrets)
- [x] Private endpoints for all backend services
- [x] Network isolation with VNet
- [x] NSGs with restrictive rules
- [x] Private DNS for name resolution
- [ ] Use Azure Key Vault for Orthanc admin password
- [ ] Enable diagnostic logging for all resources
- [ ] Configure Azure Monitor alerts
- [ ] Implement backup strategy for PostgreSQL
- [ ] Set up Azure DDoS Protection (if public ingress)
- [ ] Configure Azure Firewall (if needed)
- [ ] Review and audit role assignments quarterly
- [ ] Enable Azure Defender for Cloud

### Network Security

Production deployment includes:
- **Zero trust networking** - All traffic denied by default
- **Subnet delegation** - Container Apps subnet dedicated to Azure
- **Private endpoints** - No public IP for backend services
- **NSG rules** - Restrictive inbound/outbound rules
- **Private DNS** - Prevent DNS exfiltration

### Identity Security

Managed Identity advantages:
- **No credential storage** - Azure manages credentials
- **Automatic rotation** - No manual secret rotation
- **Audit trail** - All access logged in Azure AD
- **Least privilege** - Specific role assignments only

## Next Steps

- **Monitoring**: Configure Application Insights for advanced monitoring
- **Backup**: Set up automated PostgreSQL backups with point-in-time restore
- **Disaster Recovery**: Implement geo-redundancy and failover
- **CI/CD**: Create GitHub Actions workflow for automated deployments
- **Application Gateway**: Add WAF and SSL termination for public access
- **AKS Migration**: See [../production-aks/](../production-aks/) for Kubernetes deployment

## Support

For issues and questions:
- **Plugin Issues**: [GitHub Issues](https://github.com/rhavekost/orthanc-dicomweb-oauth/issues)
- **Azure Issues**: [Azure Support](https://azure.microsoft.com/support/)
- **Orthanc Questions**: [Orthanc Forum](https://groups.google.com/g/orthanc-users)
