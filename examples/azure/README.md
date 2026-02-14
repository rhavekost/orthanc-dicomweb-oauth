# Azure Deployment Examples

Three deployment options for Orthanc with OAuth plugin on Azure, ranging from quickstart to production-grade with managed identity and private networking.

## Deployment Options

### 1. [Quickstart](quickstart/) - Container Apps with Client Credentials

**Best for**: Development, testing, learning

- ⚡ Deploy in ~10 minutes
- 💰 Cost: ~$67/month
- 🔑 OAuth with client ID + secret
- 🌐 Public endpoints
- 📦 Azure Container Apps (consumption plan)

**Use when**: You want to quickly test Orthanc with Azure DICOM service integration.

[→ Quickstart Documentation](quickstart/README.md)

---

### 2. [Production](production/) - Container Apps with Managed Identity & VNet

**Best for**: Production workloads, HIPAA compliance, enterprise security

- 🔒 Managed identity (no secrets)
- 🌐 Private VNet with network isolation
- 🔐 Private endpoints for all backend services
- 🏥 HIPAA-compliant architecture
- 📊 Enhanced auto-scaling (2-10 replicas)
- 💰 Cost: ~$350/month
- ⏱️ Deploy in ~30 minutes

**Use when**: You need production-grade security, network isolation, and compliance.

[→ Production Documentation](production/README.md)

---

### 3. [Production AKS](production-aks/) - Kubernetes with Helm Chart

**Best for**: Kubernetes-based infrastructure, GitOps workflows

- ☸️ Azure Kubernetes Service (AKS)
- 📦 Helm chart deployment
- 🔄 GitOps-ready
- 🏗️ Full infrastructure control
- 💰 Cost: ~$500/month
- ⏱️ Deploy in ~45 minutes

**Use when**: You have existing AKS infrastructure or need Kubernetes-based deployments.

[→ Production AKS Documentation](production-aks/README.md) *(coming soon)*

---

## Quick Comparison

| Feature | Quickstart | Production | Production AKS |
|---------|-----------|------------|----------------|
| **Deploy Time** | ~10 min | ~30 min | ~45 min |
| **Monthly Cost** | ~$67 | ~$350 | ~$500 |
| **Authentication** | Client Secret | Managed Identity | Managed Identity |
| **Networking** | Public | Private VNet | Private VNet |
| **Backend Access** | Public + Firewall | Private Endpoints | Private Endpoints |
| **Compliance** | Basic | HIPAA-ready | HIPAA-ready |
| **Scaling** | 1-3 replicas | 2-10 replicas | Custom HPA |
| **Platform** | Container Apps | Container Apps | AKS |
| **Infrastructure** | Managed | Managed + VNet | Self-managed |

---

## Test Data

Synthetic DICOM test data is available in [`test-data/`](test-data/) for testing your deployment:

```bash
# Generate synthetic test data (20 DICOM files)
cd test-data
python3 generate-synthetic-dicom.py

# Upload to your deployment
./upload-test-data.sh --deployment-dir ../quickstart
# or
./upload-test-data.sh --deployment-dir ../production
```

[→ Test Data Documentation](test-data/README.md)

---

## Prerequisites

All deployments require:

- **Azure subscription** with appropriate permissions
- **Azure CLI** 2.50+ ([Install](https://docs.microsoft.com/cli/azure/install-azure-cli))
- **Docker** ([Install](https://docs.docker.com/get-docker/))
- **jq** ([Install](https://stedolan.github.io/jq/download/))
- **Azure Health Data Services** DICOM workspace already deployed
- **Azure Container Registry** for Docker images

---

## Getting Started

### 1. Choose Your Deployment

- **New to Orthanc or Azure?** → Start with [Quickstart](quickstart/)
- **Production workload?** → Use [Production](production/)
- **Existing Kubernetes?** → Use [Production AKS](production-aks/)

### 2. Deploy

Each deployment has its own detailed README with:
- Architecture diagrams
- Step-by-step deployment guide
- Configuration options
- Troubleshooting guides
- Cost breakdowns

### 3. Test with Synthetic Data

```bash
# Generate test DICOM files
cd test-data
python3 generate-synthetic-dicom.py

# Upload to your deployment
./upload-test-data.sh --deployment-dir ../quickstart
```

### 4. Verify

```bash
# Check Orthanc is running
curl -u admin:PASSWORD https://your-orthanc-url/system

# Verify OAuth forwarding to DICOM service
curl -u admin:PASSWORD https://your-orthanc-url/dicom-web/studies
```

---

## Migration Path

Migrate between deployments as your needs evolve:

```
Quickstart (dev/test)
    ↓
Production (managed identity + VNet)
    ↓
Production AKS (full Kubernetes control)
```

Each deployment's README includes migration guidance.

---

## Architecture Overview

### Quickstart Architecture

```
Internet → Container App → PostgreSQL (public + firewall)
                        → Storage (public + firewall)
                        → DICOM Service (OAuth with client secret)
```

### Production Architecture

```
Internet → Load Balancer → Container App (VNet)
                              ↓ (managed identity)
                         Private Endpoints:
                           - PostgreSQL (10.0.2.x)
                           - Storage (10.0.2.x)
                         Public Endpoint:
                           - DICOM Service (OAuth with managed identity)
```

### Production AKS Architecture

```
Internet → Ingress Controller → Orthanc Pods (VNet)
                                   ↓ (managed identity)
                              Private Endpoints:
                                - PostgreSQL
                                - Storage
                              Public Endpoint:
                                - DICOM Service
```

---

## Cost Optimization

### Development/Testing
Use **Quickstart** with:
- Consumption-based Container Apps
- Basic PostgreSQL tier
- LRS storage

**Cost**: ~$67/month

### Production
Use **Production** with:
- Reserved capacity for Container Apps
- General Purpose PostgreSQL
- Zone-redundant storage

**Cost**: ~$350/month

### Enterprise
Use **Production AKS** with:
- AKS with reserved instances
- Premium PostgreSQL
- Geo-redundant storage

**Cost**: ~$500+/month

---

## Support

- **Issues**: [GitHub Issues](https://github.com/rhavekost/orthanc-dicomweb-oauth/issues)
- **Azure Support**: [Azure Support Portal](https://azure.microsoft.com/support/)
- **Orthanc Forum**: [Orthanc Users Group](https://groups.google.com/g/orthanc-users)

---

## Contributing

Contributions welcome! See each deployment's README for specific contribution guidelines.

---

## License

See [LICENSE](../../LICENSE) in repository root.
