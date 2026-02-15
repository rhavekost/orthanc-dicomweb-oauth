# Production Azure Deployment

Production-ready deployment with VNet isolation, private endpoints, and managed identity authentication.

## Architecture

### Network Security
- **VNet Isolation**: All backend services in private subnets
- **Private Endpoints**: PostgreSQL, Storage, ACR accessible only via VNet
- **Service-Based Subnets**: Container Apps (/23), PostgreSQL (/24), Private Endpoints (/24)
- **Private DNS**: Automatic resolution for private endpoints

### Identity and Access
- **System-Assigned Managed Identity**: No client secrets required
- **RBAC in Bicep**: All permissions defined in infrastructure code
- **Roles**:
  - DICOM Data Owner (DICOM Service)
  - Storage Blob Data Contributor (Storage Account)
  - AcrPull (Container Registry)

### Infrastructure Components
- Azure Container Apps Environment with VNet integration
- PostgreSQL Flexible Server with VNet integration
- Storage Account with blob private endpoint
- Container Registry with registry private endpoint
- Healthcare Workspace + DICOM Service (public)
- Private DNS Zones (postgres, blob, ACR)
- Log Analytics Workspace

## Prerequisites

- Azure CLI installed and authenticated (`az login`)
- Docker Desktop running
- Bash shell (macOS/Linux)
- Azure subscription with required permissions

## Deployment

### Quick Start

```bash
# Clone repository
git clone https://github.com/yourusername/orthanc-dicomweb-oauth.git
cd orthanc-dicomweb-oauth/examples/azure/production

# Deploy
./deploy.sh
```

### Custom Configuration

```bash
# Set environment variables
export ENV_NAME="staging"  # or "production"
export LOCATION="eastus"   # or your preferred region

# Deploy
./deploy.sh
```

## Verification

### 1. Check Managed Identity

```bash
CONTAINER_APP_NAME="orthanc-production-app"
RG_NAME="rg-orthanc-production"

# Get managed identity principal ID
az containerapp show -n $CONTAINER_APP_NAME -g $RG_NAME \
  --query identity.principalId -o tsv
```

### 2. Verify Private Endpoints

```bash
# Check private endpoint IPs
az network private-endpoint list -g $RG_NAME --query "[].{Name:name, IP:customDnsConfigs[0].ipAddresses[0]}" -o table
```

### 3. Test DICOM Upload

```bash
CONTAINER_APP_URL=$(az containerapp show -n $CONTAINER_APP_NAME -g $RG_NAME --query properties.configuration.ingress.fqdn -o tsv)

# Upload test DICOM file
curl -u admin:PASSWORD -X POST "https://${CONTAINER_APP_URL}/instances" \
  --data-binary @test.dcm
```

## Security Features

- ✅ No public endpoints for PostgreSQL, Storage, ACR
- ✅ All backend traffic stays within VNet
- ✅ Managed identity (no client secrets)
- ✅ Private DNS for endpoint resolution
- ✅ TLS 1.2+ enforced on all services
- ✅ Storage public access disabled
- ✅ ACR admin user disabled

## Cost Optimization

Estimated monthly cost: **$150-200**

- Container Apps Environment: ~$50/month
- PostgreSQL B2s: ~$30/month
- Storage (Standard LRS): ~$20/month
- Container Registry (Basic): ~$5/month
- DICOM Service: ~$40/month
- VNet/Private Endpoints: ~$10/month

## Troubleshooting

### Issue: Container App can't pull image from ACR

**Solution**: Verify RBAC assignment
```bash
PRINCIPAL_ID=$(az containerapp show -n $CONTAINER_APP_NAME -g $RG_NAME --query identity.principalId -o tsv)
az role assignment list --assignee $PRINCIPAL_ID --scope $(az acr show -n $ACR_NAME -g $RG_NAME --query id -o tsv)
```

### Issue: Can't connect to PostgreSQL

**Solution**: Verify VNet integration
```bash
az postgres flexible-server show -n $POSTGRES_NAME -g $RG_NAME \
  --query network -o json
```

## Next Steps

- Add Application Insights for monitoring
- Enable zone redundancy for HA
- Add Application Gateway + WAF for external access
- Configure backup policies
- Set up CI/CD pipeline

## References

- [Design Document](../../docs/plans/2026-02-15-production-deployment-design.md)
- [Azure Container Apps Networking](https://learn.microsoft.com/azure/container-apps/networking)
- [Azure Private Endpoints](https://learn.microsoft.com/azure/private-link/private-endpoint-overview)
