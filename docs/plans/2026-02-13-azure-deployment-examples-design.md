# Azure Deployment Examples Design

**Date:** 2026-02-13
**Status:** Approved
**Type:** New Feature

## Overview

This design covers comprehensive deployment examples for the Orthanc DICOMweb OAuth plugin across multiple platforms. For Azure specifically, three complete deployment scenarios will be provided: a quickstart example for development/testing, a production Container Apps example for managed PaaS workloads, and a production AKS example for Kubernetes-based deployments. Additionally, a cloud-agnostic Helm chart will be provided for deployment to any Kubernetes cluster (AKS, EKS, GKE, on-premises).

## Goals

1. Provide production-ready Azure infrastructure-as-code using Bicep and Azure Verified Modules
2. Support two authentication approaches: OAuth client credentials and Managed Identity
3. Support multiple deployment platforms: Container Apps (PaaS) and AKS (Kubernetes)
4. Provide cloud-agnostic Helm chart for Kubernetes deployments across all cloud providers
5. Support two networking approaches: public endpoints and VNet with private endpoints
6. Include comprehensive documentation, testing, and maintenance tooling
7. Enable users to deploy a complete Orthanc environment with Azure DICOM service integration
8. Establish patterns that extend to AWS and GCP examples (future work)

## Non-Goals

- Multi-cloud examples (AWS, GCP) in this design (separate future efforts)
- Multi-region disaster recovery (future enhancement)
- On-premises deployment examples (focus on cloud providers)

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
examples/
├── kubernetes/                        # Cloud-agnostic Helm chart
│   ├── README.md
│   └── orthanc-oauth/                 # Helm chart
│       ├── Chart.yaml
│       ├── values.yaml
│       ├── values-azure.yaml          # Azure-specific overrides
│       ├── values-aws.yaml            # AWS-specific overrides (future)
│       ├── values-gcp.yaml            # GCP-specific overrides (future)
│       └── templates/
│
└── azure/
    ├── README.md                      # Overview, comparison table
    ├── docs/                          # Additional documentation
    ├── test-data/                     # Sample DICOM studies
    ├── quickstart/                    # Container Apps + client creds + public
    ├── production/                    # Container Apps + MI + VNet
    └── production-aks/                # AKS + Helm chart + MI + VNet
```

### Deployment Scenarios

**Decision:** Provide three complete Azure examples plus cloud-agnostic Kubernetes deployment

**Azure Scenarios:**

| Aspect | Quickstart | Production (Container Apps) | Production (AKS) |
|--------|-----------|----------------------------|------------------|
| **Platform** | Container Apps | Container Apps | AKS (Kubernetes) |
| **Authentication** | OAuth Client Credentials | Managed Identity | Managed Identity |
| **Networking** | Public endpoints + firewall | VNet + Private endpoints | VNet + Private endpoints |
| **HA/Scale** | Single instance | Multi-instance, zone-redundant | Multi-pod, HPA, cluster autoscaler |
| **Cost** | ~$66/month | ~$300-500/month | ~$400-600/month |
| **Setup Time** | ~15 minutes | ~30 minutes | ~45 minutes |
| **Complexity** | Low | Medium | High |
| **Control** | Limited (managed service) | Limited (managed service) | Full (Kubernetes) |
| **Use Case** | Dev, testing, demos | Production PaaS workloads | Production requiring k8s control |

**Kubernetes (Cloud-Agnostic):**
- Helm chart deployable to any Kubernetes cluster (AKS, EKS, GKE, on-prem)
- Supports external cloud resources (managed databases, blob storage, DICOM services)
- Supports in-cluster alternatives (PostgreSQL StatefulSet, PVCs for storage)
- Configurable authentication methods (client credentials, managed identity, service accounts)

**Rationale:**
- Clear separation makes each example easier to understand
- Users can choose based on their needs (simplicity vs control)
- Helm chart enables multi-cloud strategy (same deployment model on AWS EKS, GCP GKE)
- Container Apps examples show Azure-native PaaS approach
- AKS example demonstrates Kubernetes integration with Azure services

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

#### Production AKS Example

**Components deployed:**
1. VNet with subnets (AKS nodes, AKS pods, AKS services, Private Endpoints, PostgreSQL)
2. User-Assigned Managed Identity (for AKS workload identity)
3. AKS Cluster (with workload identity enabled, private cluster optional)
4. Healthcare Workspace + DICOM Service
5. PostgreSQL Flexible Server (VNet integrated)
6. Storage Account
7. Key Vault
8. Private Endpoints (DICOM, Storage, Key Vault)
9. RBAC role assignments (MI → DICOM, Storage, PostgreSQL, Key Vault)
10. Azure Container Registry (optional, for custom Orthanc image)
11. Helm chart deployment (Orthanc to AKS)
12. Optional: Log Analytics + Container Insights + Prometheus

**Networking:**
- AKS cluster in VNet with dedicated subnets
- All PaaS services accessed via private endpoints
- Private DNS zones for name resolution
- NSG rules on subnets
- Optional: Private AKS cluster (API server not publicly accessible)
- Ingress controller for Orthanc web access (internal or public)

**Kubernetes resources (deployed via Helm):**
- Namespace: `orthanc`
- Deployment: Orthanc pods with OAuth plugin
- Service: ClusterIP service for Orthanc
- ConfigMap: Orthanc configuration
- Secret: References to Key Vault secrets (via CSI driver)
- HorizontalPodAutoscaler: Auto-scaling based on CPU/memory
- Ingress: NGINX or Application Gateway ingress
- ServiceAccount: With federated credentials for workload identity

**Deployment order:**
```
Resource Group
  ↓
VNet + Subnets (incl. AKS-specific subnets)
  ↓
Managed Identity
  ↓
AKS Cluster
  ↓
Parallel: Healthcare Workspace, PostgreSQL, Storage Account, Key Vault, ACR (optional)
  ↓
Private Endpoints
  ↓
RBAC Assignments + Federated Credentials (Workload Identity)
  ↓
AKS Add-ons (Key Vault CSI driver, workload identity, monitoring)
  ↓
Helm Chart Deployment (Orthanc)
```

### Cloud-Agnostic Helm Chart

**Chart structure:**
```
kubernetes/orthanc-oauth/
├── Chart.yaml                        # Chart metadata
├── values.yaml                       # Default values
├── values-azure.yaml                 # Azure-specific overrides
├── values-aws.yaml                   # AWS-specific overrides (future)
├── values-gcp.yaml                   # GCP-specific overrides (future)
├── templates/
│   ├── deployment.yaml               # Orthanc Deployment
│   ├── service.yaml                  # Orthanc Service
│   ├── configmap.yaml                # Orthanc configuration
│   ├── secret.yaml                   # Secrets (if not using external secret store)
│   ├── serviceaccount.yaml           # Service account for workload identity
│   ├── hpa.yaml                      # Horizontal Pod Autoscaler
│   ├── ingress.yaml                  # Ingress resource
│   ├── pvc.yaml                      # PersistentVolumeClaim (optional)
│   ├── networkpolicy.yaml            # Network policies (optional)
│   └── _helpers.tpl                  # Template helpers
└── README.md                         # Helm chart documentation
```

**Configuration philosophy:**
- **Cloud-agnostic by default**: Works on any k8s cluster
- **Cloud-specific overrides**: values-{cloud}.yaml for cloud integrations
- **Flexible storage**: Support external blob storage OR PVCs
- **Flexible database**: Support external managed PostgreSQL OR in-cluster StatefulSet
- **Flexible authentication**: Client credentials, workload identity (Azure), IAM roles (AWS), service accounts (GCP)
- **Flexible secrets**: External secret stores (Key Vault, Secrets Manager) OR Kubernetes secrets

**Key values.yaml sections:**
```yaml
image:
  repository: orthancteam/orthanc
  tag: 24.12.1-full
  pullPolicy: IfNotPresent

replicaCount: 2

resources:
  requests:
    cpu: 1000m
    memory: 2Gi
  limits:
    cpu: 2000m
    memory: 4Gi

autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70

database:
  type: external              # 'external' or 'in-cluster'
  external:
    host: ""                  # Set in cloud-specific values
    port: 5432
    database: orthanc
    sslMode: require
    credentialsSecret: ""     # Name of k8s secret with username/password

storage:
  type: external              # 'external' or 'pvc'
  external:
    provider: azure-blob      # 'azure-blob', 'aws-s3', 'gcp-gcs'
    connectionStringSecret: "" # Name of k8s secret
    container: orthanc-dicom
  pvc:
    size: 100Gi
    storageClass: ""

oauthPlugin:
  servers:
    dicom:
      url: ""                 # Set in cloud-specific values
      tokenEndpoint: ""
      scope: ""
      authentication:
        type: workload-identity  # 'client-credentials', 'workload-identity', 'iam-role', 'service-account'
        clientId: ""            # For client-credentials
        clientSecretKey: ""     # Secret key name for client-credentials

ingress:
  enabled: true
  className: nginx
  annotations: {}
  hosts:
    - host: orthanc.example.com
      paths:
        - path: /
          pathType: Prefix
  tls: []

monitoring:
  enabled: true
  prometheus:
    enabled: true
    port: 9090
```

**values-azure.yaml example:**
```yaml
database:
  external:
    host: mypostgres.postgres.database.azure.com
    credentialsSecret: azure-postgresql-creds

storage:
  external:
    provider: azure-blob
    connectionStringSecret: azure-storage-creds
    container: orthanc-dicom

oauthPlugin:
  servers:
    dicom:
      url: https://workspace-dicom.dicom.azurehealthcareapis.com/v2/
      tokenEndpoint: https://login.microsoftonline.com/TENANT_ID/oauth2/v2.0/token
      scope: https://dicom.healthcareapis.azure.com/.default
      authentication:
        type: workload-identity
        clientId: MANAGED_IDENTITY_CLIENT_ID

serviceAccount:
  annotations:
    azure.workload.identity/client-id: MANAGED_IDENTITY_CLIENT_ID
    azure.workload.identity/tenant-id: TENANT_ID
```

### Azure Verified Modules Used

All modules referenced from Bicep Public Registry (`br/public:avm/...`):

**Common across all examples:**
- `avm/res/health-data-services/workspace` - Healthcare workspace
- `avm/res/health-data-services/workspace/dicomservice` - DICOM service
- `avm/res/db-for-postgre-sql/flexible-server` - PostgreSQL Flexible Server
- `avm/res/storage/storage-account` - Storage accounts
- `avm/res/key-vault/vault` - Key Vault
- `avm/res/network/virtual-network` - VNet (production examples)
- `avm/res/network/private-endpoint` - Private endpoints (production examples)
- `avm/res/managed-identity/user-assigned-identity` - Managed Identity (production examples)

**Container Apps examples (quickstart, production):**
- `avm/res/app/container-app` - Container App
- `avm/res/app/managed-environment` - Container App Environment

**AKS example (production-aks):**
- `avm/res/container-service/managed-cluster` - AKS cluster
- `avm/res/container-registry/registry` - Azure Container Registry (optional)

**Custom modules (only where needed):**
- `modules/orthanc-config.bicep` - Generates Orthanc environment variables from parameters (Container Apps examples)
- `modules/helm-values.bicep` - Generates Helm values file from parameters (AKS example)

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

**Production (Container Apps) specific:**
- `vnetAddressPrefix` - VNet CIDR
- `containerAppSubnetPrefix` - Container App subnet CIDR
- `privateEndpointSubnetPrefix` - Private endpoint subnet CIDR
- `postgresSubnetPrefix` - PostgreSQL subnet CIDR
- `postgresHighAvailability` - HA mode (ZoneRedundant)
- `containerAppMinReplicas` - Min replicas for scaling
- `containerAppMaxReplicas` - Max replicas for scaling
- `enableDiagnosticLogs` - Enable diagnostic settings
- `logAnalyticsWorkspaceId` - Log Analytics workspace ID

**Production AKS specific:**
- `vnetAddressPrefix` - VNet CIDR
- `aksNodeSubnetPrefix` - AKS nodes subnet CIDR
- `aksPodSubnetPrefix` - AKS pods subnet CIDR (Azure CNI)
- `aksServiceSubnetPrefix` - AKS services subnet CIDR
- `privateEndpointSubnetPrefix` - Private endpoint subnet CIDR
- `postgresSubnetPrefix` - PostgreSQL subnet CIDR
- `aksVersion` - Kubernetes version
- `aksNodeSize` - VM size for nodes (Standard_D4s_v3)
- `aksNodeCount` - Initial node count
- `aksMinNodes` - Min nodes for autoscaling
- `aksMaxNodes` - Max nodes for autoscaling
- `aksPrivateCluster` - Enable private AKS cluster
- `enableContainerInsights` - Enable Container Insights monitoring
- `deployAcr` - Deploy Azure Container Registry
- `helmReleaseName` - Helm release name
- `helmNamespace` - Kubernetes namespace

**Parameter files provided:**

Quickstart:
- `parameters.json.template` - Template to fill in
- `parameters.dev.example.json` - Development example
- `parameters.demo.example.json` - Demo/training example

Production (Container Apps):
- `parameters.json.template` - Template to fill in
- `parameters.prod.example.json` - Production example
- `parameters.dr.example.json` - DR region example

Production AKS:
- `parameters.json.template` - Template to fill in
- `parameters.prod.example.json` - Production AKS example
- `helm-values.yaml.template` - Helm values template

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

### Phase 1: Cloud-Agnostic Helm Chart

1. Create `examples/kubernetes/` structure
2. Implement Helm chart:
   - `Chart.yaml` with metadata
   - `values.yaml` with defaults
   - `values-azure.yaml` with Azure-specific config
   - Kubernetes templates (Deployment, Service, ConfigMap, etc.)
   - Chart documentation
3. Test Helm chart on local Kubernetes (kind/minikube)

### Phase 2: Azure Quickstart (Container Apps)

1. Create `examples/azure/quickstart/` structure
2. Implement infrastructure:
   - `main.bicep` with AVM module references
   - `modules/orthanc-config.bicep`
   - `parameters.json.template` and examples
   - `Dockerfile`
3. Implement scripts:
   - `setup-app-registration.sh`
   - `deploy.sh`
   - `test-deployment.sh`
   - `cleanup.sh`
4. Write comprehensive README

### Phase 3: Azure Production (Container Apps)

1. Create `examples/azure/production/` structure
2. Implement infrastructure:
   - `main.bicep` with VNet and MI
   - `modules/orthanc-config.bicep` and `monitoring.bicep`
   - `parameters.json.template` and examples
   - `Dockerfile`
3. Implement scripts:
   - `deploy.sh`
   - `post-deployment.sh`
   - `test-deployment.sh`
   - `cleanup.sh`
4. Write comprehensive README

### Phase 4: Azure Production AKS

1. Create `examples/azure/production-aks/` structure
2. Implement infrastructure:
   - `main.bicep` with AKS cluster and VNet
   - `modules/helm-values.bicep`
   - `parameters.json.template` and examples
3. Implement scripts:
   - `deploy.sh` (deploys Bicep + Helm)
   - `post-deployment.sh`
   - `test-deployment.sh`
   - `update-helm.sh`
   - `cleanup.sh`
4. Write comprehensive README

### Phase 5: Documentation and Testing

1. Top-level Azure README with comparison
2. Kubernetes README
3. Additional docs (cost, scaling, backup, networking, FAQ)
4. Test data setup
5. Automated test scripts
6. CI/CD workflow examples

### Phase 6: Maintenance Tooling

1. Update scripts (Container Apps and AKS)
2. Secret rotation scripts
3. Monitoring and alerting setup

### Phase 7: Optional Enhancements

1. Multi-region DR example
2. Advanced HPA policies for AKS
3. Cost optimization dashboards
4. Advanced monitoring with Grafana

## Success Criteria

**Helm Chart:**
- [ ] Helm chart deploys successfully to local Kubernetes cluster
- [ ] Chart is configurable for different cloud providers via values files
- [ ] Chart documentation is clear and comprehensive

**Azure Quickstart (Container Apps):**
- [ ] Deploys successfully in clean Azure subscription
- [ ] Orthanc can authenticate to Azure DICOM service with client credentials
- [ ] DICOM upload/query/retrieve works end-to-end
- [ ] Web viewers (Stone, OHIF) accessible and functional
- [ ] All automated tests pass

**Azure Production (Container Apps):**
- [ ] Deploys successfully with VNet and private endpoints
- [ ] Managed Identity authentication works for all Azure services
- [ ] No public endpoints exposed (verified)
- [ ] Multi-instance scaling works
- [ ] All automated tests pass

**Azure Production AKS:**
- [ ] AKS cluster deploys successfully with workload identity
- [ ] Helm chart deploys Orthanc to AKS
- [ ] Managed Identity authentication works via federated credentials
- [ ] DICOM connectivity via private endpoints works
- [ ] HPA scales pods based on load
- [ ] All automated tests pass

**Common:**
- [ ] PostgreSQL stores Orthanc index data (all examples)
- [ ] Blob storage stores DICOM files (all examples)
- [ ] OAuth plugin successfully acquires tokens (all auth methods)
- [ ] Documentation is comprehensive and accurate
- [ ] Cleanup scripts remove all resources

## Security Considerations

**Quickstart:**
- OAuth client secrets stored in Key Vault
- PostgreSQL password stored in Key Vault
- Firewall rules restrict access
- HTTPS/TLS for all connections
- Authentication enabled on Orthanc

**Production (Container Apps):**
- No public endpoints (private endpoints only)
- Managed Identity for all authentication (no secrets)
- VNet isolation
- NSG rules on subnets
- Zone-redundant services
- Diagnostic logging enabled
- HIPAA-aligned architecture

**Production AKS:**
- Private AKS cluster (optional, API server not public)
- Workload Identity for pod authentication (no secrets in pods)
- VNet isolation with dedicated subnets
- NSG rules and Network Policies
- Private endpoints for all Azure services
- Azure Policy for Kubernetes (security baseline)
- Container image scanning (ACR + Defender for Containers)
- Pod Security Standards enforcement
- Secrets from Key Vault via CSI driver (not in etcd)
- RBAC enabled on cluster
- Audit logging to Log Analytics
- HIPAA-aligned architecture

## Cost Analysis

**Quickstart (Container Apps) - ~$66/month:**
- Healthcare DICOM Service: ~$25
- PostgreSQL B2s: ~$15
- Storage Account: ~$5
- Container App (1vCPU, 2GB): ~$20
- Key Vault: ~$1

**Production (Container Apps) - ~$300-500/month:**
- Healthcare DICOM Service: ~$25
- PostgreSQL D2s_v3 (zone-redundant): ~$150-200
- Storage Account (geo-redundant): ~$20
- Container App (2vCPU, 4GB, multi-instance): ~$80-120
- VNet + Private Endpoints: ~$10-20
- Key Vault: ~$1
- Log Analytics (optional): ~$20-50

**Production AKS - ~$400-600/month:**
- Healthcare DICOM Service: ~$25
- PostgreSQL D2s_v3 (zone-redundant): ~$150-200
- Storage Account (geo-redundant): ~$20
- AKS Control Plane: Free (Uptime SLA: ~$73/month)
- AKS Nodes (3x Standard_D4s_v3): ~$150-200
- VNet + Private Endpoints: ~$10-20
- Key Vault: ~$1
- Azure Container Registry (optional): ~$5-20
- Container Insights (optional): ~$20-50

Note: AKS costs vary significantly based on node size, count, and autoscaling configuration.

## Future Enhancements

**AWS Examples (Next Priority):**
- Quickstart: ECS Fargate + client credentials + public endpoints
- Production: ECS Fargate + IAM roles + VPC + private endpoints
- Production EKS: EKS cluster + Helm chart + IAM roles for service accounts + VPC
- Use same Helm chart with values-aws.yaml overrides

**GCP Examples:**
- Quickstart: Cloud Run + client credentials + public endpoints
- Production: Cloud Run + service accounts + VPC + private endpoints
- Production GKE: GKE cluster + Helm chart + workload identity + VPC
- Use same Helm chart with values-gcp.yaml overrides

**Multi-Cloud Enhancements:**
- Terraform versions of infrastructure templates (alongside Bicep)
- Pulumi examples for programmatic infrastructure
- CI/CD pipelines for each cloud provider
- Multi-cloud cost comparison dashboard

**Advanced Features:**
- Multi-region disaster recovery (active-passive and active-active)
- Auto-scaling based on DICOM upload metrics
- Advanced monitoring with Grafana dashboards
- Performance testing framework
- Backup and restore automation
- Blue/green deployment strategies

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
