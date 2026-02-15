# Production Azure Deployment Design

**Date**: 2026-02-15
**Status**: Approved
**Location**: `examples/azure/production/`

## Overview

Create a production-ready Azure deployment that demonstrates enterprise security patterns with VNet isolation, private endpoints, and managed identity authentication while maintaining the transparent OAuth proxy functionality from the quickstart.

## Design Decisions

### Network Isolation
- **Choice**: Full isolation for backend services
- **Rationale**: PostgreSQL, Storage, and ACR use private endpoints only; Container App has external ingress with VNet integration
- **Trade-offs**: More complex but production-grade security

### External Access
- **Choice**: Container App with external ingress + VNet integration
- **Rationale**: Publicly accessible but network-integrated; simpler than App Gateway for an example
- **Trade-offs**: Less security layers than WAF but easier to understand

### Managed Identity
- **Choice**: System-assigned managed identity with RBAC in Bicep
- **Rationale**: Simpler lifecycle management, all RBAC defined in infrastructure code
- **Trade-offs**: Identity tied to Container App lifecycle (acceptable for examples)

### DNS Configuration
- **Choice**: Automatic Private DNS integration
- **Rationale**: Standard Azure pattern, fully automated in Bicep
- **Trade-offs**: Creates additional resources but essential for private endpoints

### Subnet Structure
- **Choice**: Service-based subnets (Container Apps, PostgreSQL, Private Endpoints)
- **Rationale**: Clean separation, easier to manage NSGs, clear organizational structure
- **Trade-offs**: More subnets but better security boundaries

## Architecture

### Network Architecture

**VNet Configuration**:
- Address Space: `10.0.0.0/16` (65,536 addresses)
- Region: Same as resource group
- DNS: Azure-provided DNS with Private DNS zone integration

**Subnet Structure**:

1. **Container Apps Subnet** (`snet-container-apps`)
   - CIDR: `10.0.0.0/23` (512 addresses)
   - Purpose: Container Apps Environment
   - Requirements: /23 or larger for Container Apps
   - VNet integration enabled for outbound traffic
   - External ingress for public access

2. **PostgreSQL Subnet** (`snet-postgres`)
   - CIDR: `10.0.2.0/24` (256 addresses)
   - Purpose: PostgreSQL Flexible Server
   - Delegation: `Microsoft.DBforPostgreSQL/flexibleServers`
   - Required for PostgreSQL VNet integration

3. **Private Endpoints Subnet** (`snet-private-endpoints`)
   - CIDR: `10.0.3.0/24` (256 addresses)
   - Purpose: Private endpoints for Storage and ACR
   - No delegation required

**Private DNS Zones** (auto-created and linked to VNet):
- `privatelink.postgres.database.azure.com`
- `privatelink.blob.core.windows.net`
- `privatelink.azurecr.io`

**Network Security**:
- No public endpoints for PostgreSQL, Storage, ACR
- Container App accessible externally but VNet-integrated
- All backend traffic stays within VNet

### Security & Identity

**Managed Identity Configuration**:
- **Type**: System-assigned managed identity on Container App
- **Lifecycle**: Created/destroyed with Container App
- **Usage**: Authenticate to Azure services without secrets

**RBAC Assignments** (configured in Bicep):

1. **DICOM Service Access**:
   - Role: `DICOM Data Owner`
   - Scope: DICOM Service resource
   - Allows: Read/write DICOM data

2. **Storage Access**:
   - Role: `Storage Blob Data Contributor`
   - Scope: Storage Account
   - Allows: Read/write blobs for Orthanc storage

3. **Container Registry Access**:
   - Role: `AcrPull`
   - Scope: Container Registry
   - Allows: Pull container images

4. **PostgreSQL Access**:
   - Uses VNet integration (not managed identity)
   - PostgreSQL password stored as Container App secret
   - Future enhancement: AAD authentication for PostgreSQL

**Private Endpoints**:
- **Storage**: `blob` subresource
- **ACR**: `registry` subresource
- **DNS**: Auto-registered in Private DNS zones
- **Connectivity**: Accessible only from VNet

### Python Plugin Changes

**New Component**: `AzureManagedIdentityProvider` class

**Features**:
- Auto-detects managed identity vs client credentials
- Uses `azure.identity.DefaultAzureCredential`
- No client secrets required
- Falls back to client credentials for local development

**Detection Logic**:
```python
if "IDENTITY_ENDPOINT" in os.environ:
    provider = AzureManagedIdentityProvider(config)
else:
    provider = AzureOAuthProvider(config)  # Client credentials
```

**Dependencies**:
- Add `azure-identity` to requirements.txt
- Compatible with existing `azure-core` usage

## Components & Bicep Modules

### File Structure

```
examples/azure/production/
├── main.bicep                    # Main orchestration
├── deploy.sh                     # Deployment script
├── README.md                     # Production deployment guide
├── SECURITY.md                   # Security best practices
├── modules/
│   ├── network.bicep            # VNet, subnets, NSGs
│   ├── private-dns.bicep        # Private DNS zones
│   ├── private-endpoint.bicep   # Reusable PE module
│   ├── container-registry.bicep # ACR with private endpoint
│   ├── postgres.bicep           # PostgreSQL with VNet integration
│   ├── storage.bicep            # Storage with private endpoint
│   ├── container-app.bicep      # Container App + managed identity
│   ├── healthcare-workspace.bicep # DICOM (reused from quickstart)
│   ├── postgres-config.bicep    # PostgreSQL extensions (reused)
│   └── rbac-assignments.bicep   # Centralized RBAC
└── orthanc.json                 # Orthanc configuration template
```

### Key Modules

1. **network.bicep**: VNet with 3 subnets, NSG configuration
2. **private-endpoint.bicep**: Generic PE template (reusable for Storage, ACR)
3. **private-dns.bicep**: Creates and links DNS zones to VNet
4. **rbac-assignments.bicep**: All managed identity role assignments
5. **container-app.bicep**: Container App with system-assigned MI, VNet integration

### Module Reuse from Quickstart

- `healthcare-workspace.bicep` - No changes needed
- `postgres-config.bicep` - PostgreSQL extensions configuration
- `orthanc-config.json` - Orthanc configuration template (updated for MI)

### Parameters (main.bicep)

Required:
- `environmentName`: Environment identifier (e.g., "production")
- `location`: Azure region
- `resourceGroupName`: Resource group name
- `orthancUsername`: Orthanc admin username
- `orthancPassword`: Orthanc admin password (stored as secret)

Optional:
- `vnetAddressPrefix`: VNet address space (default: "10.0.0.0/16")
- `containerAppsSubnetPrefix`: Container Apps subnet (default: "10.0.0.0/23")
- `postgresSubnetPrefix`: PostgreSQL subnet (default: "10.0.2.0/24")
- `privateEndpointsSubnetPrefix`: Private endpoints subnet (default: "10.0.3.0/24")

Not needed (removed):
- `oauthClientId` - Not used with managed identity
- `oauthClientSecret` - Not used with managed identity
- `servicePrincipalObjectId` - Not used with managed identity

## Data Flow & Traffic Patterns

### Inbound DICOM Upload Flow

```
External User/System
    ↓ HTTPS
Container App (external ingress)
    ↓ (within container)
Orthanc receives DICOM
    ↓ (managed identity token)
Python OAuth Plugin acquires token via DefaultAzureCredential
    ↓ HTTPS (OAuth token in header)
Azure DICOM Service (public endpoint)
```

### Orthanc Data Persistence Flow

```
Orthanc Plugin
    ↓ (VNet, private endpoint)
PostgreSQL (metadata) - privatelink.postgres.database.azure.com
    ↓ (VNet, private endpoint)
Azure Blob Storage (DICOM files) - privatelink.blob.core.windows.net
```

### Container Image Pull Flow

```
Container Apps Environment
    ↓ (managed identity + VNet)
Private Endpoint → ACR - privatelink.azurecr.io
    ↓ (RBAC: AcrPull)
Pull image
```

### Key Security Points

- PostgreSQL traffic never leaves VNet
- Storage traffic never leaves VNet
- ACR access via private endpoint only
- DICOM Service uses managed identity (no secrets)
- DNS resolution handled by Private DNS zones

### Changes from Quickstart

| Aspect | Quickstart | Production |
|--------|-----------|------------|
| DICOM Auth | Client credentials | Managed identity |
| PostgreSQL Access | Public endpoint | VNet integration |
| Storage Access | Public endpoint | Private endpoint |
| ACR Access | Public endpoint | Private endpoint |
| Network Isolation | None | VNet with subnets |
| DNS | Public DNS | Private DNS zones |

## Deployment Process

### Prerequisites

- Azure CLI installed and authenticated (`az login`)
- Docker Desktop running (for image build)
- Bash shell (macOS/Linux)
- No pre-existing infrastructure required

### Deployment Script (deploy.sh)

```bash
#!/bin/bash

# Phase 1: Deploy network infrastructure
# - VNet, subnets, NSGs
# - Private DNS zones

# Phase 2: Deploy data services with private endpoints
# - PostgreSQL Flexible Server (VNet integrated)
# - Storage Account + blob private endpoint
# - Container Registry + registry private endpoint

# Phase 3: Deploy DICOM Service
# - Healthcare Workspace
# - DICOM Service (public)
# - RBAC assignments for managed identity

# Phase 4: Build and push Docker image
# - Build with --platform linux/amd64
# - Push to ACR via private endpoint

# Phase 5: Deploy Container App
# - Create with system-assigned managed identity
# - Configure VNet integration
# - Set environment variables (no client secrets!)
# - Deploy with image from ACR
```

### Key Differences from Quickstart Deployment

1. **No client credentials** - Managed identity only, no app registration needed
2. **VNet-first** - Network deployed before services
3. **Private endpoints** - Created with each service
4. **RBAC upfront** - All role assignments defined in Bicep

### Deployment Time

- **Estimated**: 15-20 minutes
- **Factors**: Private endpoint creation adds 3-5 minutes vs quickstart

### Configuration Files

- **Not needed**: `app-registration.json` (managed identity replaces this)
- **Reused**: `orthanc.json` template from quickstart
- **New**: `deployment-params.json` with network parameters

## Testing & Validation

### Post-Deployment Verification

#### 1. Network Connectivity Test

```bash
# Verify private endpoints resolve to private IPs
az containerapp exec -n orthanc-prod-app -g rg-orthanc-prod \
  --command "nslookup <storage-account>.blob.core.windows.net"
# Expected: Should resolve to 10.0.3.x (private IP)
```

#### 2. Managed Identity Test

```bash
# Check Container App has system-assigned identity
az containerapp show -n orthanc-prod-app -g rg-orthanc-prod \
  --query identity.principalId -o tsv
# Expected: Should return a GUID
```

#### 3. RBAC Verification

```bash
# Verify role assignments exist
PRINCIPAL_ID=$(az containerapp show -n orthanc-prod-app -g rg-orthanc-prod \
  --query identity.principalId -o tsv)

az role assignment list --assignee $PRINCIPAL_ID -o table
# Expected: Should show "DICOM Data Owner", "Storage Blob Data Contributor", "AcrPull"
```

#### 4. Functional Tests

- **Upload DICOM file**: `curl -u admin:password -X POST https://<container-app-url>/instances --data-binary @test.dcm`
- **Verify PostgreSQL metadata**: Check `/system` endpoint shows PostgreSQL plugin
- **Verify Blob Storage**: Check `/system` endpoint shows Azure Blob Storage plugin
- **Verify DICOM forwarding**: Check Azure DICOM Service for uploaded files
- **Check plugins active**: `curl -u admin:password https://<container-app-url>/system | jq`

#### 5. Security Validation

```bash
# Confirm PostgreSQL has no public IP
az postgres flexible-server show -n <postgres-name> -g rg-orthanc-prod \
  --query network.publicNetworkAccess -o tsv
# Expected: "Disabled"

# Confirm Storage Account blocks public access
az storage account show -n <storage-name> -g rg-orthanc-prod \
  --query allowBlobPublicAccess -o tsv
# Expected: "false"

# Verify private endpoints resolve to private IPs
nslookup <storage-account>.blob.core.windows.net
# Expected: 10.0.3.x address
```

### Monitoring

- **Container App logs**: Monitor OAuth token acquisition via managed identity
- **Application Insights**: Request telemetry and performance metrics
- **PostgreSQL metrics**: Connection health and query performance
- **Storage metrics**: Blob operations and access patterns

## Implementation Plan

### Phase 1: Python Plugin Enhancement (1-2 days)

1. Create `AzureManagedIdentityProvider` class
2. Add `azure-identity` to requirements
3. Update OAuth provider factory to support managed identity
4. Add tests for managed identity provider
5. Update documentation

### Phase 2: Bicep Infrastructure (2-3 days)

1. Create `network.bicep` module (VNet, subnets, NSGs)
2. Create `private-dns.bicep` module (DNS zones)
3. Create `private-endpoint.bicep` module (reusable template)
4. Update `storage.bicep` to add private endpoint
5. Update `container-registry.bicep` to add private endpoint
6. Update `postgres.bicep` for VNet integration
7. Create `container-app.bicep` with managed identity
8. Create `rbac-assignments.bicep` for all role assignments
9. Create main orchestration `main.bicep`

### Phase 3: Deployment Automation (1 day)

1. Create `deploy.sh` script with phased deployment
2. Add validation checks between phases
3. Add error handling and rollback logic
4. Create comprehensive README.md
5. Create SECURITY.md with best practices

### Phase 4: Testing & Documentation (1 day)

1. Test fresh deployment from scratch
2. Verify all security controls
3. Test DICOM upload end-to-end
4. Document verification steps
5. Create troubleshooting guide

**Total Estimated Time**: 5-7 days

## Success Criteria

- [ ] All backend services use private endpoints
- [ ] Container App uses managed identity (no client secrets)
- [ ] PostgreSQL accessible only via VNet
- [ ] Storage accessible only via VNet
- [ ] ACR accessible only via VNet
- [ ] DICOM upload works end-to-end
- [ ] PostgreSQL and Blob Storage persistence verified
- [ ] All tests pass
- [ ] Documentation complete
- [ ] Deployment script works on fresh Azure subscription

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Private endpoint DNS resolution issues | High | Use automatic Private DNS integration, document troubleshooting |
| Managed identity permission delays | Medium | Add retry logic, wait for RBAC propagation |
| Container App VNet integration complexity | Medium | Test thoroughly, provide clear error messages |
| PostgreSQL VNet delegation conflicts | Low | Verify subnet delegation in Bicep |
| Deployment time too long | Low | Optimize module dependencies, parallel where possible |

## Future Enhancements

1. **AAD Authentication for PostgreSQL**: Replace password with managed identity
2. **Application Gateway + WAF**: Add enterprise-grade external access
3. **Private endpoint for DICOM Service**: Requires VNet-enabled Healthcare Workspace
4. **Zone redundancy**: Enable for production HA
5. **Backup and DR**: Add automated backup policies
6. **Monitoring dashboards**: Pre-built Grafana/Azure Monitor dashboards

## References

- [Azure Container Apps networking](https://learn.microsoft.com/azure/container-apps/networking)
- [Azure Private Endpoints](https://learn.microsoft.com/azure/private-link/private-endpoint-overview)
- [Managed identities](https://learn.microsoft.com/azure/active-directory/managed-identities-azure-resources/overview)
- [PostgreSQL VNet integration](https://learn.microsoft.com/azure/postgresql/flexible-server/concepts-networking)
- [Azure SDK DefaultAzureCredential](https://learn.microsoft.com/python/api/azure-identity/azure.identity.defaultazurecredential)
