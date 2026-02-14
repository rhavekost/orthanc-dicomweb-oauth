# Orthanc OAuth Helm Chart

Deploy Orthanc DICOM server with DICOMweb OAuth plugin to Kubernetes.

## Features

- ✅ Cloud-agnostic (works on AKS, EKS, GKE, on-premises)
- ✅ Multiple authentication methods (client credentials, workload identity, IAM roles)
- ✅ Flexible storage backends (cloud blob storage or PVCs)
- ✅ Flexible database backends (managed cloud databases or in-cluster)
- ✅ Horizontal pod autoscaling
- ✅ Ingress support (NGINX, Application Gateway, etc.)
- ✅ Prometheus metrics

## Prerequisites

- Kubernetes 1.24+
- Helm 3.8+
- External DICOM service (Azure Health Data Services, Google Cloud Healthcare API, etc.)
- External PostgreSQL database (recommended) or in-cluster StatefulSet
- External blob storage (recommended) or persistent volumes

## Installation

### Basic Installation

```bash
helm install orthanc orthanc-oauth/ \
  --set database.external.host=mydb.postgres.database.azure.com \
  --set database.external.credentialsSecret=db-creds \
  --set storage.external.connectionStringSecret=storage-creds \
  --set oauthPlugin.servers.dicom.url=https://dicom.example.com/v2/
```

### Azure-Specific Installation

```bash
helm install orthanc orthanc-oauth/ -f values-azure.yaml
```

## Configuration

See [values.yaml](values.yaml) for all configuration options.

### Key Configuration Sections

#### Database Configuration

```yaml
database:
  type: external  # 'external' or 'in-cluster'
  external:
    host: mydb.postgres.database.azure.com
    port: 5432
    database: orthanc
    credentialsSecret: db-credentials
```

#### Storage Configuration

```yaml
storage:
  type: external  # 'external' or 'pvc'
  external:
    provider: azure-blob  # 'azure-blob', 'aws-s3', 'gcp-gcs'
    connectionStringSecret: storage-connection
    container: orthanc-dicom
```

#### OAuth Plugin Configuration

```yaml
oauthPlugin:
  servers:
    dicom:
      url: https://workspace.dicom.azurehealthcareapis.com/v2/
      tokenEndpoint: https://login.microsoftonline.com/TENANT/oauth2/v2.0/token
      scope: https://dicom.healthcareapis.azure.com/.default
      authentication:
        type: workload-identity
        clientId: MANAGED_IDENTITY_CLIENT_ID
```

## Examples

- [Azure with Workload Identity](../azure/production-aks/)
- AWS with IAM Roles - Coming soon
- GCP with Workload Identity - Coming soon

## Monitoring

Prometheus metrics exposed on `/metrics` endpoint:

```yaml
monitoring:
  enabled: true
  prometheus:
    enabled: true
    port: 9090
```

## Troubleshooting

### Pod fails to start

Check logs:
```bash
kubectl logs -n orthanc deployment/orthanc-oauth
```

### OAuth authentication fails

Verify workload identity configuration:
```bash
kubectl describe serviceaccount -n orthanc orthanc-oauth
```

### Database connection fails

Test database connectivity:
```bash
kubectl run -it --rm debug --image=postgres:15 --restart=Never -- \
  psql -h HOST -U USERNAME -d DATABASE
```
