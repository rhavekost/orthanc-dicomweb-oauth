# Azure Deployment Examples Design

**Date:** 2026-02-13
**Status:** Approved
**Type:** New Feature

## Overview

This design covers comprehensive Azure deployment examples for the Orthanc DICOMweb OAuth plugin. Two complete deployment scenarios will be provided: a quickstart example for development/testing and a production example for secure, HIPAA-compliant workloads.

## Goals

1. Provide production-ready Azure infrastructure-as-code using Bicep and Azure Verified Modules
2. Support two authentication approaches: OAuth client credentials and Managed Identity
3. Support two networking approaches: public endpoints and VNet with private endpoints
4. Include comprehensive documentation, testing, and maintenance tooling
5. Enable users to deploy a complete Orthanc environment with Azure DICOM service integration

## Non-Goals

- Multi-cloud examples (AWS, GCP) in this design (separate efforts)
- Kubernetes/AKS deployment (Container Apps only)
- Multi-region disaster recovery (future enhancement)

## Design Decisions

### Structure and Organization

**Decision:** Single main.bicep with modules, leveraging Azure Verified Modules (AVM)

**Rationale:**
- AVM provides officially maintained, best-practice modules
- Reduces custom code maintenance burden
- Automatic support for diagnostic settings, RBAC, tags, private endpoints
- Better consistency with Azure patterns

**Folder structure:**
```
examples/azure/
├── README.md                          # Overview, comparison table
├── docs/                              # Additional documentation
├── test-data/                         # Sample DICOM studies
├── quickstart/                        # Client creds + public networking
└── production/                        # Managed Identity + VNet
```

### Deployment Scenarios

**Decision:** Provide two complete examples rather than parameter-based variations

**Scenarios:**

| Aspect | Quickstart | Production |
|--------|-----------|------------|
| **Authentication** | OAuth Client Credentials | Managed Identity |
| **Networking** | Public endpoints + firewall rules | VNet + Private endpoints |
| **HA/Scale** | Single instance | Multi-instance, zone-redundant |
| **Cost** | ~$66/month | ~$300-500/month |
| **Setup Time** | ~15 minutes | ~30 minutes |
| **Use Case** | Dev, testing, demos | Production, HIPAA workloads |

**Rationale:**
- Clear separation makes each example easier to understand
- Users can choose based on their needs without complex parameter logic
- Demonstrates both ends of the spectrum (simple vs secure)

### Resource Architecture

#### Quickstart Example

**Components deployed:**
1. Azure AD App Registration (via CLI script)
2. Healthcare Workspace + DICOM Service
3. PostgreSQL Flexible Server (Orthanc index database)
4. Storage Account (blob storage for DICOM files)
5. Key Vault (secrets: PostgreSQL password, OAuth client secret)
6. Container App Environment
7. Container App (Orthanc with OAuth plugin)

**Networking:**
- All services use public endpoints
- Firewall rules restrict access to Container App subnet
- OAuth client credentials for DICOM service authentication

**Deployment order:**
```
Resource Group
  ↓
App Registration (CLI script - prerequisite)
  ↓
Parallel: Healthcare Workspace, PostgreSQL, Storage Account, Key Vault
  ↓
Container App Environment
  ↓
Container App (Orthanc)
```

#### Production Example

**Components deployed:**
1. VNet with subnets (Container App, Private Endpoints, PostgreSQL)
2. User-Assigned Managed Identity
3. Healthcare Workspace + DICOM Service
4. PostgreSQL Flexible Server (VNet integrated)
5. Storage Account
6. Key Vault
7. Private Endpoints (DICOM, Storage, Key Vault)
8. RBAC role assignments (MI → DICOM, Storage, PostgreSQL, Key Vault)
9. Container App Environment (VNet integrated)
10. Container App (Orthanc with MI)
11. Optional: Log Analytics + Application Insights + Alerts

**Networking:**
- All PaaS services accessed via private endpoints
- No public endpoints exposed
- Private DNS zones for name resolution
- NSG rules on subnets

**Deployment order:**
```
Resource Group
  ↓
VNet + Subnets
  ↓
Managed Identity
  ↓
Parallel: Healthcare Workspace, PostgreSQL, Storage Account, Key Vault
  ↓
Private Endpoints
  ↓
RBAC Assignments
  ↓
Container App Environment
  ↓
Container App (Orthanc)
```

### Azure Verified Modules Used

All modules referenced from Bicep Public Registry (`br/public:avm/...`):

- `avm/res/health-data-services/workspace` - Healthcare workspace
- `avm/res/health-data-services/workspace/dicomservice` - DICOM service
- `avm/res/db-for-postgre-sql/flexible-server` - PostgreSQL Flexible Server
- `avm/res/storage/storage-account` - Storage accounts
- `avm/res/app/container-app` - Container App
- `avm/res/app/managed-environment` - Container App Environment
- `avm/res/key-vault/vault` - Key Vault
- `avm/res/network/virtual-network` - VNet (production)
- `avm/res/network/private-endpoint` - Private endpoints (production)
- `avm/res/managed-identity/user-assigned-identity` - Managed Identity (production)

**Custom modules (only where needed):**
- `modules/orthanc-config.bicep` - Generates Orthanc environment variables from parameters

### Parameter Design

**Common parameters (both examples):**
- `location` - Azure region
- `projectName` - Project name for resource naming
- `environment` - Environment tag (dev/prod)
- `healthcareWorkspaceName` - Healthcare workspace name
- `dicomServiceName` - DICOM service name
- `postgresAdminUsername` - PostgreSQL admin username
- `postgresAdminPassword` - PostgreSQL admin password (secure)
- `postgresSku` - PostgreSQL SKU
- `orthancContainerImage` - Container image (with OAuth plugin)
- `orthancCpuCores` - CPU allocation
- `orthancMemoryGi` - Memory allocation
- `tags` - Resource tags

**Quickstart-specific:**
- `tenantId` - Azure AD tenant ID
- `clientId` - OAuth client ID (from app registration)
- `clientSecret` - OAuth client secret (secure)

**Production-specific:**
- `vnetAddressPrefix` - VNet CIDR
- `containerAppSubnetPrefix` - Container App subnet CIDR
- `privateEndpointSubnetPrefix` - Private endpoint subnet CIDR
- `postgresSubnetPrefix` - PostgreSQL subnet CIDR
- `postgresHighAvailability` - HA mode (ZoneRedundant)
- `containerAppMinReplicas` - Min replicas for scaling
- `containerAppMaxReplicas` - Max replicas for scaling
- `enableDiagnosticLogs` - Enable diagnostic settings
- `logAnalyticsWorkspaceId` - Log Analytics workspace ID

**Parameter files provided:**
- `parameters.json.template` - Template to fill in
- `parameters.dev.example.json` - Development example
- `parameters.demo.example.json` - Demo/training example (quickstart)
- `parameters.prod.example.json` - Production example
- `parameters.dr.example.json` - DR region example (production)

### Orthanc Configuration

**Container image strategy:**

**Decision:** Use `orthancteam/orthanc:full` as base image

**Rationale:**
- Includes Stone Web Viewer and OHIF viewer
- Includes DICOMweb server/client plugins
- Includes PostgreSQL plugin
- Production-ready base
- Only need to add OAuth plugin on top

**Custom Dockerfile (both examples):**
```dockerfile
FROM orthancteam/orthanc:24.12.1-full

# Install Python dependencies for OAuth plugin
RUN apt-get update && \
    apt-get install -y python3-pip && \
    pip3 install requests PyJWT cryptography redis prometheus-client && \
    rm -rf /var/lib/apt/lists/*

# Copy OAuth plugin
COPY src/ /etc/orthanc/plugins/

# Plugin will be loaded via ORTHANC__PLUGINS environment variable
ENV ORTHANC__PLUGINS='["/etc/orthanc/plugins/dicomweb_oauth_plugin.py"]'
```

**Configuration injection:**

**Decision:** Use Container App environment variables

**Rationale:**
- Cloud-native approach
- Easy integration with Key Vault secret references
- No additional storage account needed for config files
- Easy to update without rebuilding images

**Environment variable structure (generated by orthanc-config.bicep):**
```
ORTHANC__POSTGRESQL__HOST
ORTHANC__POSTGRESQL__DATABASE
ORTHANC__POSTGRESQL__USERNAME (from Key Vault)
ORTHANC__POSTGRESQL__PASSWORD (from Key Vault)
ORTHANC__AZURE_BLOB_STORAGE__CONNECTION_STRING (from Key Vault)
ORTHANC__AZURE_BLOB_STORAGE__CONTAINER
ORTHANC__DICOMWEB_OAUTH__SERVERS__AZURE_DICOM__URL
ORTHANC__DICOMWEB_OAUTH__SERVERS__AZURE_DICOM__TOKEN_ENDPOINT
ORTHANC__DICOMWEB_OAUTH__SERVERS__AZURE_DICOM__CLIENT_ID (quickstart, from Key Vault)
ORTHANC__DICOMWEB_OAUTH__SERVERS__AZURE_DICOM__CLIENT_SECRET (quickstart, from Key Vault)
ORTHANC__DICOMWEB_OAUTH__SERVERS__AZURE_DICOM__USE_MANAGED_IDENTITY (production)
ORTHANC__DICOMWEB_OAUTH__SERVERS__AZURE_DICOM__SCOPE
AZURE_CLIENT_ID (production, for DefaultAzureCredential)
ORTHANC__AUTHENTICATION_ENABLED
ORTHANC__REMOTE_ACCESS_ALLOWED
```

### Deployment Scripts

**Quickstart scripts:**

1. **`setup-app-registration.sh`**
   - Creates Azure AD app registration
   - Creates client secret
   - Grants Healthcare APIs permissions (DICOM Data Owner scope)
   - Grants admin consent
   - Outputs: clientId, tenantId, clientSecret

2. **`deploy.sh`**
   - Validates prerequisites (Azure CLI, parameters.json)
   - Creates resource group
   - Deploys main.bicep
   - Retrieves outputs
   - Displays post-deployment instructions

3. **`test-deployment.sh`**
   - Health check: Orthanc API responds
   - OAuth test: Plugin can acquire token
   - DICOM connectivity: Can query DICOM service
   - Storage test: Can store/retrieve from blob
   - Database test: PostgreSQL connection works
   - Viewer test: Stone Web Viewer accessible

4. **`update-orthanc.sh`**
   - Updates Orthanc container image to new version
   - Runs health checks after update
   - Rollback on failure

5. **`rotate-secrets.sh`**
   - Rotates OAuth client secret
   - Updates Key Vault
   - Restarts Container App

6. **`cleanup.sh`**
   - Confirms before deletion
   - Lists resources to be deleted
   - Deletes resource group

**Production scripts:**

Same as quickstart, plus:

1. **`post-deployment.sh`**
   - Verifies private DNS resolution
   - Tests managed identity token acquisition
   - Verifies Orthanc can connect to PostgreSQL
   - Tests DICOM service connectivity via private endpoint
   - Runs smoke tests
   - Generates deployment report

**Script design principles:**
- Idempotent (can be re-run safely)
- Clear error messages with remediation steps
- Progress indicators
- Output capture (URLs, IDs)
- Pre-flight and post-deployment validation

### Documentation Structure

**Top-level README (`examples/azure/README.md`):**
- Overview of both examples
- Architecture comparison table
- Prerequisites
- Choosing an example (decision tree)
- AVM modules used
- Support and troubleshooting links

**Example-specific READMEs:**

Each example includes comprehensive README with:

1. **Overview** - What gets deployed, when to use
2. **Architecture Diagram** - ASCII art diagram
3. **Prerequisites** - Detailed checklist with verification commands
4. **Cost Estimation** - Table with SKUs and monthly costs
5. **Deployment Steps** - Step-by-step with code blocks, expected outputs
6. **Post-Deployment Testing** - Test procedures and expected results
7. **Configuration Reference** - Parameter descriptions, env var mapping
8. **Troubleshooting** - Common issues with solutions
9. **Cleanup** - Removal procedures

**Production README additional sections:**
- Network Planning (CIDR requirements, connectivity options)
- Security Considerations (HIPAA alignment, encryption, audit logging)
- High Availability Configuration (zone redundancy, backup/DR, scaling)
- Monitoring and Observability (Log Analytics, metrics, alerts)
- Compliance Documentation (HIPAA mapping, BAA requirements, audit retention)

**Additional documentation (`docs/`):**
- `cost-optimization.md` - Tips for reducing costs
- `scaling-guide.md` - How to scale components
- `backup-restore.md` - Backup procedures
- `network-troubleshooting.md` - VNet connectivity issues
- `faq.md` - Common questions

### Testing and Validation

**Test data:**
- Sample DICOM study in `test-data/sample-study/`
- README with usage instructions
- Or download link to public test dataset

**Automated testing scripts:**
- Health checks for all services
- OAuth token acquisition test
- DICOM connectivity test (upload, query, retrieve)
- Storage persistence test
- Database connectivity test
- Viewer accessibility test

**CI/CD integration (optional):**
- GitHub Actions workflow examples
- Bicep validation and linting
- What-if deployment preview
- Optional: Deploy to dev environment
- Smoke tests after deployment

### Monitoring and Observability

**Optional monitoring module (`production/modules/monitoring.bicep`):**

Deploys:
- Log Analytics workspace
- Application Insights
- Diagnostic settings for all resources
- Azure Monitor alerts:
  - Container App health
  - DICOM service availability
  - PostgreSQL connection failures
  - OAuth token acquisition errors
  - High memory/CPU usage

**Prometheus metrics:**
- OAuth plugin already exposes `/metrics` endpoint
- Can be scraped by Azure Monitor or external Prometheus

## Implementation Plan

### Phase 1: Core Infrastructure Templates

1. Create folder structure
2. Implement quickstart example:
   - `main.bicep` with AVM module references
   - `modules/orthanc-config.bicep`
   - `parameters.json.template` and examples
   - `Dockerfile`
3. Implement production example:
   - `main.bicep` with VNet and MI
   - `modules/orthanc-config.bicep` and `monitoring.bicep`
   - `parameters.json.template` and examples
   - `Dockerfile`

### Phase 2: Deployment Scripts

1. Quickstart scripts (setup, deploy, test, cleanup)
2. Production scripts (deploy, post-deployment, test, cleanup)
3. Maintenance scripts (update, rotate-secrets)

### Phase 3: Documentation

1. Top-level README
2. Quickstart README
3. Production README
4. Additional docs (cost, scaling, backup, networking, FAQ)

### Phase 4: Testing and Validation

1. Test data setup
2. Automated test scripts
3. Manual testing procedures
4. CI/CD workflow examples

### Phase 5: Optional Enhancements

1. Monitoring module
2. Multi-region DR example
3. Advanced scaling policies
4. Cost optimization dashboards

## Success Criteria

- [ ] Both examples deploy successfully in clean Azure subscription
- [ ] Orthanc can authenticate to Azure DICOM service
- [ ] DICOM upload/query/retrieve works end-to-end
- [ ] Web viewers (Stone, OHIF) accessible and functional
- [ ] PostgreSQL stores Orthanc index data
- [ ] Blob storage stores DICOM files
- [ ] OAuth plugin successfully acquires tokens (both MI and client creds)
- [ ] All automated tests pass
- [ ] Documentation is comprehensive and accurate
- [ ] Cleanup scripts remove all resources

## Security Considerations

**Quickstart:**
- OAuth client secrets stored in Key Vault
- PostgreSQL password stored in Key Vault
- Firewall rules restrict access
- HTTPS/TLS for all connections
- Authentication enabled on Orthanc

**Production:**
- No public endpoints (private endpoints only)
- Managed Identity for all authentication (no secrets)
- VNet isolation
- NSG rules on subnets
- Zone-redundant services
- Diagnostic logging enabled
- HIPAA-aligned architecture

## Cost Analysis

**Quickstart (~$66/month):**
- Healthcare DICOM Service: ~$25
- PostgreSQL B2s: ~$15
- Storage Account: ~$5
- Container App (1vCPU, 2GB): ~$20
- Key Vault: ~$1

**Production (~$300-500/month):**
- Healthcare DICOM Service: ~$25
- PostgreSQL D2s_v3 (zone-redundant): ~$150-200
- Storage Account (geo-redundant): ~$20
- Container App (2vCPU, 4GB, multi-instance): ~$80-120
- VNet + Private Endpoints: ~$10-20
- Key Vault: ~$1
- Log Analytics (optional): ~$20-50

## Future Enhancements

- AWS deployment examples (ECS, HealthImaging)
- GCP deployment examples (Cloud Run, Healthcare API)
- Terraform versions of templates
- Helm charts for Kubernetes/AKS
- Multi-region disaster recovery
- Auto-scaling based on metrics
- Cost optimization dashboards
- Advanced monitoring with Grafana

## Questions and Risks

**Questions:**
- Should we include Azure Container Registry in the templates, or assume users bring their own?
  - Decision: Provide instructions but don't deploy ACR (users often have existing registries)

**Risks:**
- AVM module versions may change - mitigation: Pin to specific versions
- Azure pricing changes - mitigation: Note costs are estimates
- DICOM service regional availability - mitigation: Document supported regions

## References

- [Azure Verified Modules](https://aka.ms/avm)
- [Azure Health Data Services](https://learn.microsoft.com/azure/healthcare-apis/)
- [Container Apps](https://learn.microsoft.com/azure/container-apps/)
- [Orthanc Documentation](https://orthanc.uclouvain.be/book/)
- [OAuth Plugin Documentation](../README.md)
