# Kubernetes Deployment with Helm

Cloud-agnostic Helm chart for deploying Orthanc with DICOMweb OAuth plugin to any Kubernetes cluster.

## Supported Platforms

- Azure Kubernetes Service (AKS)
- Amazon Elastic Kubernetes Service (EKS) - Coming soon
- Google Kubernetes Engine (GKE) - Coming soon
- On-premises Kubernetes clusters

## Quick Start

```bash
# Install to local cluster
helm install orthanc ./orthanc-oauth -f values.yaml

# Install with Azure-specific configuration
helm install orthanc ./orthanc-oauth -f values-azure.yaml
```

## Documentation

See [orthanc-oauth/README.md](orthanc-oauth/README.md) for complete chart documentation.
