# Azure Deployment Examples Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create production-ready Azure deployment examples with Container Apps, AKS, and cloud-agnostic Helm chart for Orthanc DICOMweb OAuth plugin.

**Architecture:** Three Azure deployment options (quickstart Container Apps, production Container Apps, production AKS) plus a cloud-agnostic Helm chart. Uses Azure Verified Modules for infrastructure, implements both client credentials and managed identity authentication, supports public and private networking.

**Tech Stack:**
- Infrastructure: Bicep, Azure Verified Modules (AVM)
- Container Orchestration: Azure Container Apps, Azure Kubernetes Service (AKS)
- Packaging: Helm 3.x, Docker
- Scripting: Bash, Azure CLI
- Cloud Services: Azure Health Data Services (DICOM), PostgreSQL Flexible Server, Azure Blob Storage, Key Vault

---

## Phase 1: Project Structure and Helm Chart Foundation

### Task 1: Create Base Folder Structure

**Files:**
- Create: `examples/kubernetes/README.md`
- Create: `examples/kubernetes/orthanc-oauth/.helmignore`
- Create: `examples/azure/README.md`
- Create: `examples/azure/docs/.gitkeep`
- Create: `examples/azure/test-data/.gitkeep`

**Step 1: Create kubernetes folder structure**

```bash
mkdir -p examples/kubernetes/orthanc-oauth/templates
mkdir -p examples/azure/{docs,test-data,quickstart,production,production-aks}
```

**Step 2: Create kubernetes README**

File: `examples/kubernetes/README.md`
```markdown
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
```

**Step 3: Create .helmignore**

File: `examples/kubernetes/orthanc-oauth/.helmignore`
```
# Patterns to ignore when building packages.
*.md
.git/
.gitignore
.DS_Store
*.swp
*.bak
*.tmp
*.orig
*~
.project
.idea/
*.tmproj
.vscode/
```

**Step 4: Create Azure top-level README placeholder**

File: `examples/azure/README.md`
```markdown
# Azure Deployment Examples

Three deployment options for Azure. Full documentation coming soon.

## Examples

- [Quickstart](quickstart/) - Container Apps with client credentials
- [Production](production/) - Container Apps with managed identity
- [Production AKS](production-aks/) - AKS with Helm chart
```

**Step 5: Commit**

```bash
git add examples/
git commit -m "feat: create base folder structure for examples

Add folder structure for Kubernetes Helm chart and Azure deployment
examples including quickstart, production, and production-aks.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

### Task 2: Helm Chart Metadata

**Files:**
- Create: `examples/kubernetes/orthanc-oauth/Chart.yaml`
- Create: `examples/kubernetes/orthanc-oauth/README.md`

**Step 1: Create Chart.yaml**

File: `examples/kubernetes/orthanc-oauth/Chart.yaml`
```yaml
apiVersion: v2
name: orthanc-oauth
description: Orthanc DICOM server with DICOMweb OAuth plugin for cloud DICOM services
type: application
version: 1.0.0
appVersion: "24.12.1"
keywords:
  - orthanc
  - dicom
  - medical-imaging
  - oauth
  - healthcare
home: https://github.com/rhavekost/orthanc-dicomweb-oauth
sources:
  - https://github.com/rhavekost/orthanc-dicomweb-oauth
maintainers:
  - name: rhavekost
    url: https://github.com/rhavekost
icon: https://www.orthanc-server.com/static/img/OrthancLogoDocumentation.png
```

**Step 2: Create Helm chart README**

File: `examples/kubernetes/orthanc-oauth/README.md`
```markdown
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
```

**Step 3: Validate YAML syntax**

```bash
# Ensure Chart.yaml is valid
helm lint examples/kubernetes/orthanc-oauth/ --strict
```

Expected output: No errors (will warn about missing templates, which is expected at this stage)

**Step 4: Commit**

```bash
git add examples/kubernetes/orthanc-oauth/
git commit -m "feat(helm): add chart metadata and documentation

Add Chart.yaml with chart metadata and comprehensive README
documenting installation, configuration, and troubleshooting.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

### Task 3: Helm Chart Default Values

**Files:**
- Create: `examples/kubernetes/orthanc-oauth/values.yaml`

**Step 1: Create comprehensive values.yaml**

File: `examples/kubernetes/orthanc-oauth/values.yaml`
```yaml
# Default values for orthanc-oauth
# This is a YAML-formatted file.

# Orthanc container image configuration
image:
  repository: orthancteam/orthanc
  tag: "24.12.1-full"
  pullPolicy: IfNotPresent
  # pullSecrets: []

# Number of replicas
replicaCount: 2

# Resource limits and requests
resources:
  requests:
    cpu: 1000m
    memory: 2Gi
  limits:
    cpu: 2000m
    memory: 4Gi

# Horizontal Pod Autoscaler configuration
autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
  targetMemoryUtilizationPercentage: 80

# Database configuration
database:
  # Type: 'external' for managed cloud database, 'in-cluster' for StatefulSet
  type: external

  external:
    # Database connection details
    host: ""  # Required: PostgreSQL host (e.g., mydb.postgres.database.azure.com)
    port: 5432
    database: orthanc
    sslMode: require
    # Kubernetes secret containing 'username' and 'password' keys
    credentialsSecret: ""  # Required: name of secret

  # In-cluster PostgreSQL (for development/testing only)
  inCluster:
    enabled: false
    storageSize: 20Gi
    storageClass: ""

# Storage configuration for DICOM files
storage:
  # Type: 'external' for cloud blob storage, 'pvc' for persistent volume
  type: external

  external:
    # Provider: 'azure-blob', 'aws-s3', 'gcp-gcs'
    provider: azure-blob
    # Kubernetes secret containing connection string or credentials
    connectionStringSecret: ""  # Required: name of secret
    # Container/bucket name
    container: orthanc-dicom

  # Persistent Volume Claim (alternative to cloud storage)
  pvc:
    enabled: false
    size: 100Gi
    storageClass: ""
    accessMode: ReadWriteOnce

# OAuth plugin configuration
oauthPlugin:
  # Log level: DEBUG, INFO, WARNING, ERROR
  logLevel: INFO

  # Rate limiting
  rateLimitRequests: 100
  rateLimitWindowSeconds: 60

  # Servers configuration
  servers:
    dicom:
      # DICOM service URL
      url: ""  # Required: e.g., https://workspace.dicom.azurehealthcareapis.com/v2/
      # OAuth token endpoint
      tokenEndpoint: ""  # Required: e.g., https://login.microsoftonline.com/TENANT/oauth2/v2.0/token
      # OAuth scope
      scope: ""  # Required: e.g., https://dicom.healthcareapis.azure.com/.default
      # Token refresh buffer (seconds)
      tokenRefreshBufferSeconds: 300

      # Authentication configuration
      authentication:
        # Type: 'client-credentials', 'workload-identity', 'iam-role', 'service-account'
        type: workload-identity
        # For client-credentials only
        clientId: ""
        clientSecretKey: ""  # Key name in clientSecretSecret
        clientSecretSecret: ""  # Secret name containing client secret

# Orthanc core configuration
orthanc:
  # Enable remote access
  remoteAccessAllowed: true
  # Enable authentication
  authenticationEnabled: true
  # Registered users (username: password)
  registeredUsers: {}
    # admin: "changeme"

  # HTTP server configuration
  httpPort: 8042
  httpCompression: true
  httpThreadsCount: 50

  # DICOM configuration
  dicomAet: "ORTHANC"
  dicomPort: 4242
  dicomThreadsCount: 4

# Service configuration
service:
  type: ClusterIP
  httpPort: 8042
  dicomPort: 4242
  annotations: {}

# Ingress configuration
ingress:
  enabled: true
  className: nginx
  annotations: {}
    # cert-manager.io/cluster-issuer: letsencrypt-prod
  hosts:
    - host: orthanc.example.com
      paths:
        - path: /
          pathType: Prefix
  tls: []
    # - secretName: orthanc-tls
    #   hosts:
    #     - orthanc.example.com

# Service account configuration
serviceAccount:
  create: true
  annotations: {}
    # For Azure Workload Identity:
    # azure.workload.identity/client-id: MANAGED_IDENTITY_CLIENT_ID
    # azure.workload.identity/tenant-id: TENANT_ID
  name: ""

# Pod annotations
podAnnotations: {}
  # For Azure Workload Identity:
  # azure.workload.identity/use: "true"

# Pod security context
podSecurityContext:
  fsGroup: 1000
  runAsNonRoot: true
  runAsUser: 1000

# Container security context
securityContext:
  allowPrivilegeEscalation: false
  capabilities:
    drop:
    - ALL
  readOnlyRootFilesystem: false

# Node selector
nodeSelector: {}

# Tolerations
tolerations: []

# Affinity
affinity: {}

# Monitoring configuration
monitoring:
  enabled: true
  prometheus:
    enabled: true
    port: 9090
  serviceMonitor:
    enabled: false
    interval: 30s

# Network policy
networkPolicy:
  enabled: false
  policyTypes:
    - Ingress
    - Egress

# Liveness and readiness probes
livenessProbe:
  httpGet:
    path: /system
    port: 8042
  initialDelaySeconds: 30
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3

readinessProbe:
  httpGet:
    path: /system
    port: 8042
  initialDelaySeconds: 10
  periodSeconds: 5
  timeoutSeconds: 3
  failureThreshold: 3
```

**Step 2: Validate values.yaml syntax**

```bash
# Check YAML syntax
helm lint examples/kubernetes/orthanc-oauth/ --strict
```

Expected: No errors

**Step 3: Commit**

```bash
git add examples/kubernetes/orthanc-oauth/values.yaml
git commit -m "feat(helm): add comprehensive default values

Add values.yaml with all configurable parameters including:
- Image and replica configuration
- Resource limits and autoscaling
- Database and storage backends
- OAuth plugin configuration
- Service, ingress, and monitoring settings

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

### Task 4: Helm Template Helpers

**Files:**
- Create: `examples/kubernetes/orthanc-oauth/templates/_helpers.tpl`

**Step 1: Create template helpers**

File: `examples/kubernetes/orthanc-oauth/templates/_helpers.tpl`
```yaml
{{/*
Expand the name of the chart.
*/}}
{{- define "orthanc-oauth.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "orthanc-oauth.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "orthanc-oauth.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "orthanc-oauth.labels" -}}
helm.sh/chart: {{ include "orthanc-oauth.chart" . }}
{{ include "orthanc-oauth.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "orthanc-oauth.selectorLabels" -}}
app.kubernetes.io/name: {{ include "orthanc-oauth.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "orthanc-oauth.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "orthanc-oauth.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Database connection string for Orthanc
*/}}
{{- define "orthanc-oauth.databaseConnectionString" -}}
{{- if eq .Values.database.type "external" }}
{{- printf "host=%s port=%d dbname=%s sslmode=%s" .Values.database.external.host (.Values.database.external.port | int) .Values.database.external.database .Values.database.external.sslMode }}
{{- else }}
{{- printf "host=%s-postgresql port=5432 dbname=orthanc sslmode=disable" (include "orthanc-oauth.fullname" .) }}
{{- end }}
{{- end }}
```

**Step 2: Validate template syntax**

```bash
helm lint examples/kubernetes/orthanc-oauth/
```

Expected: No errors

**Step 3: Commit**

```bash
git add examples/kubernetes/orthanc-oauth/templates/_helpers.tpl
git commit -m "feat(helm): add template helpers

Add Helm template helpers for:
- Name and fullname generation
- Common labels and selectors
- Service account name
- Database connection string generation

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Phase 2: Helm Chart Kubernetes Resources

### Task 5: ServiceAccount and ConfigMap Templates

**Files:**
- Create: `examples/kubernetes/orthanc-oauth/templates/serviceaccount.yaml`
- Create: `examples/kubernetes/orthanc-oauth/templates/configmap.yaml`

**Step 1: Create ServiceAccount template**

File: `examples/kubernetes/orthanc-oauth/templates/serviceaccount.yaml`
```yaml
{{- if .Values.serviceAccount.create -}}
apiVersion: v1
kind: ServiceAccount
metadata:
  name: {{ include "orthanc-oauth.serviceAccountName" . }}
  namespace: {{ .Release.Namespace }}
  labels:
    {{- include "orthanc-oauth.labels" . | nindent 4 }}
  {{- with .Values.serviceAccount.annotations }}
  annotations:
    {{- toYaml . | nindent 4 }}
  {{- end }}
{{- end }}
```

**Step 2: Create ConfigMap template**

File: `examples/kubernetes/orthanc-oauth/templates/configmap.yaml`
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "orthanc-oauth.fullname" . }}
  namespace: {{ .Release.Namespace }}
  labels:
    {{- include "orthanc-oauth.labels" . | nindent 4 }}
data:
  # Orthanc core configuration
  orthanc.json: |
    {
      "Name": "{{ .Values.orthanc.dicomAet }}",
      "RemoteAccessAllowed": {{ .Values.orthanc.remoteAccessAllowed }},
      "AuthenticationEnabled": {{ .Values.orthanc.authenticationEnabled }},
      {{- if .Values.orthanc.registeredUsers }}
      "RegisteredUsers": {{ .Values.orthanc.registeredUsers | toJson }},
      {{- end }}
      "HttpPort": {{ .Values.orthanc.httpPort }},
      "HttpCompressionEnabled": {{ .Values.orthanc.httpCompression }},
      "HttpThreadsCount": {{ .Values.orthanc.httpThreadsCount }},
      "DicomAet": "{{ .Values.orthanc.dicomAet }}",
      "DicomPort": {{ .Values.orthanc.dicomPort }},
      "DicomThreadsCount": {{ .Values.orthanc.dicomThreadsCount }},
      "Plugins": ["/etc/orthanc/plugins/dicomweb_oauth_plugin.py"]
    }

  # OAuth plugin configuration
  dicomweb-oauth.json: |
    {
      "DicomWebOAuth": {
        "ConfigVersion": "2.0",
        "LogLevel": "{{ .Values.oauthPlugin.logLevel }}",
        "RateLimitRequests": {{ .Values.oauthPlugin.rateLimitRequests }},
        "RateLimitWindowSeconds": {{ .Values.oauthPlugin.rateLimitWindowSeconds }},
        "Servers": {
          {{- range $name, $server := .Values.oauthPlugin.servers }}
          "{{ $name }}": {
            "Url": "{{ $server.url }}",
            "TokenEndpoint": "{{ $server.tokenEndpoint }}",
            "Scope": "{{ $server.scope }}",
            "TokenRefreshBufferSeconds": {{ $server.tokenRefreshBufferSeconds | default 300 }},
            {{- if eq $server.authentication.type "client-credentials" }}
            "ClientId": "${OAUTH_CLIENT_ID}",
            "ClientSecret": "${OAUTH_CLIENT_SECRET}",
            {{- else if eq $server.authentication.type "workload-identity" }}
            "UseManagedIdentity": true,
            {{- end }}
            "VerifySSL": true
          }{{ if not (last $name $.Values.oauthPlugin.servers) }},{{ end }}
          {{- end }}
        }
      }
    }
```

**Step 3: Validate templates**

```bash
helm template test examples/kubernetes/orthanc-oauth/ --debug
```

Expected: Templates render without errors

**Step 4: Commit**

```bash
git add examples/kubernetes/orthanc-oauth/templates/
git commit -m "feat(helm): add ServiceAccount and ConfigMap templates

Add Kubernetes templates for:
- ServiceAccount with configurable annotations for workload identity
- ConfigMap with Orthanc core config and OAuth plugin config

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

### Task 6: Deployment Template

**Files:**
- Create: `examples/kubernetes/orthanc-oauth/templates/deployment.yaml`

**Step 1: Create Deployment template**

File: `examples/kubernetes/orthanc-oauth/templates/deployment.yaml`
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "orthanc-oauth.fullname" . }}
  namespace: {{ .Release.Namespace }}
  labels:
    {{- include "orthanc-oauth.labels" . | nindent 4 }}
spec:
  {{- if not .Values.autoscaling.enabled }}
  replicas: {{ .Values.replicaCount }}
  {{- end }}
  selector:
    matchLabels:
      {{- include "orthanc-oauth.selectorLabels" . | nindent 6 }}
  template:
    metadata:
      annotations:
        checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
        {{- with .Values.podAnnotations }}
        {{- toYaml . | nindent 8 }}
        {{- end }}
      labels:
        {{- include "orthanc-oauth.selectorLabels" . | nindent 8 }}
    spec:
      {{- if .Values.image.pullSecrets }}
      imagePullSecrets:
        {{- toYaml .Values.image.pullSecrets | nindent 8 }}
      {{- end }}
      serviceAccountName: {{ include "orthanc-oauth.serviceAccountName" . }}
      securityContext:
        {{- toYaml .Values.podSecurityContext | nindent 8 }}
      containers:
      - name: orthanc
        securityContext:
          {{- toYaml .Values.securityContext | nindent 12 }}
        image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
        imagePullPolicy: {{ .Values.image.pullPolicy }}
        ports:
        - name: http
          containerPort: {{ .Values.orthanc.httpPort }}
          protocol: TCP
        - name: dicom
          containerPort: {{ .Values.orthanc.dicomPort }}
          protocol: TCP
        {{- if .Values.monitoring.enabled }}
        - name: metrics
          containerPort: {{ .Values.monitoring.prometheus.port }}
          protocol: TCP
        {{- end }}
        env:
        # Database configuration
        - name: ORTHANC__POSTGRESQL__HOST
          value: "{{ .Values.database.external.host }}"
        - name: ORTHANC__POSTGRESQL__PORT
          value: "{{ .Values.database.external.port }}"
        - name: ORTHANC__POSTGRESQL__DATABASE
          value: "{{ .Values.database.external.database }}"
        - name: ORTHANC__POSTGRESQL__USERNAME
          valueFrom:
            secretKeyRef:
              name: {{ .Values.database.external.credentialsSecret }}
              key: username
        - name: ORTHANC__POSTGRESQL__PASSWORD
          valueFrom:
            secretKeyRef:
              name: {{ .Values.database.external.credentialsSecret }}
              key: password

        # Storage configuration
        {{- if eq .Values.storage.type "external" }}
        {{- if eq .Values.storage.external.provider "azure-blob" }}
        - name: ORTHANC__AZURE_BLOB_STORAGE__CONNECTION_STRING
          valueFrom:
            secretKeyRef:
              name: {{ .Values.storage.external.connectionStringSecret }}
              key: connectionString
        - name: ORTHANC__AZURE_BLOB_STORAGE__CONTAINER
          value: "{{ .Values.storage.external.container }}"
        {{- end }}
        {{- end }}

        # OAuth plugin configuration
        {{- range $name, $server := .Values.oauthPlugin.servers }}
        {{- if eq $server.authentication.type "client-credentials" }}
        - name: OAUTH_CLIENT_ID
          valueFrom:
            secretKeyRef:
              name: {{ $server.authentication.clientSecretSecret }}
              key: clientId
        - name: OAUTH_CLIENT_SECRET
          valueFrom:
            secretKeyRef:
              name: {{ $server.authentication.clientSecretSecret }}
              key: {{ $server.authentication.clientSecretKey }}
        {{- else if eq $server.authentication.type "workload-identity" }}
        - name: AZURE_CLIENT_ID
          value: "{{ $server.authentication.clientId }}"
        {{- end }}
        {{- end }}

        volumeMounts:
        - name: config
          mountPath: /etc/orthanc/orthanc.json
          subPath: orthanc.json
        - name: config
          mountPath: /etc/orthanc/dicomweb-oauth.json
          subPath: dicomweb-oauth.json
        {{- if eq .Values.storage.type "pvc" }}
        - name: data
          mountPath: /var/lib/orthanc/db
        {{- end }}

        livenessProbe:
          {{- toYaml .Values.livenessProbe | nindent 12 }}
        readinessProbe:
          {{- toYaml .Values.readinessProbe | nindent 12 }}
        resources:
          {{- toYaml .Values.resources | nindent 12 }}

      volumes:
      - name: config
        configMap:
          name: {{ include "orthanc-oauth.fullname" . }}
      {{- if eq .Values.storage.type "pvc" }}
      - name: data
        persistentVolumeClaim:
          claimName: {{ include "orthanc-oauth.fullname" . }}
      {{- end }}

      {{- with .Values.nodeSelector }}
      nodeSelector:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      {{- with .Values.affinity }}
      affinity:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      {{- with .Values.tolerations }}
      tolerations:
        {{- toYaml . | nindent 8 }}
      {{- end }}
```

**Step 2: Validate template**

```bash
helm template test examples/kubernetes/orthanc-oauth/ --debug
```

Expected: Deployment renders correctly

**Step 3: Commit**

```bash
git add examples/kubernetes/orthanc-oauth/templates/deployment.yaml
git commit -m "feat(helm): add Deployment template

Add Kubernetes Deployment template with:
- Configurable replicas and autoscaling support
- Environment variables from ConfigMap and Secrets
- Volume mounts for configuration
- Liveness and readiness probes
- Resource limits and requests

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

### Task 7: Service, HPA, and Ingress Templates

**Files:**
- Create: `examples/kubernetes/orthanc-oauth/templates/service.yaml`
- Create: `examples/kubernetes/orthanc-oauth/templates/hpa.yaml`
- Create: `examples/kubernetes/orthanc-oauth/templates/ingress.yaml`

**Step 1: Create Service template**

File: `examples/kubernetes/orthanc-oauth/templates/service.yaml`
```yaml
apiVersion: v1
kind: Service
metadata:
  name: {{ include "orthanc-oauth.fullname" . }}
  namespace: {{ .Release.Namespace }}
  labels:
    {{- include "orthanc-oauth.labels" . | nindent 4 }}
  {{- with .Values.service.annotations }}
  annotations:
    {{- toYaml . | nindent 4 }}
  {{- end }}
spec:
  type: {{ .Values.service.type }}
  ports:
  - port: {{ .Values.service.httpPort }}
    targetPort: http
    protocol: TCP
    name: http
  - port: {{ .Values.service.dicomPort }}
    targetPort: dicom
    protocol: TCP
    name: dicom
  {{- if .Values.monitoring.enabled }}
  - port: {{ .Values.monitoring.prometheus.port }}
    targetPort: metrics
    protocol: TCP
    name: metrics
  {{- end }}
  selector:
    {{- include "orthanc-oauth.selectorLabels" . | nindent 4 }}
```

**Step 2: Create HPA template**

File: `examples/kubernetes/orthanc-oauth/templates/hpa.yaml`
```yaml
{{- if .Values.autoscaling.enabled }}
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: {{ include "orthanc-oauth.fullname" . }}
  namespace: {{ .Release.Namespace }}
  labels:
    {{- include "orthanc-oauth.labels" . | nindent 4 }}
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: {{ include "orthanc-oauth.fullname" . }}
  minReplicas: {{ .Values.autoscaling.minReplicas }}
  maxReplicas: {{ .Values.autoscaling.maxReplicas }}
  metrics:
  {{- if .Values.autoscaling.targetCPUUtilizationPercentage }}
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: {{ .Values.autoscaling.targetCPUUtilizationPercentage }}
  {{- end }}
  {{- if .Values.autoscaling.targetMemoryUtilizationPercentage }}
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: {{ .Values.autoscaling.targetMemoryUtilizationPercentage }}
  {{- end }}
{{- end }}
```

**Step 3: Create Ingress template**

File: `examples/kubernetes/orthanc-oauth/templates/ingress.yaml`
```yaml
{{- if .Values.ingress.enabled -}}
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {{ include "orthanc-oauth.fullname" . }}
  namespace: {{ .Release.Namespace }}
  labels:
    {{- include "orthanc-oauth.labels" . | nindent 4 }}
  {{- with .Values.ingress.annotations }}
  annotations:
    {{- toYaml . | nindent 4 }}
  {{- end }}
spec:
  {{- if .Values.ingress.className }}
  ingressClassName: {{ .Values.ingress.className }}
  {{- end }}
  {{- if .Values.ingress.tls }}
  tls:
    {{- range .Values.ingress.tls }}
    - hosts:
        {{- range .hosts }}
        - {{ . | quote }}
        {{- end }}
      secretName: {{ .secretName }}
    {{- end }}
  {{- end }}
  rules:
    {{- range .Values.ingress.hosts }}
    - host: {{ .host | quote }}
      http:
        paths:
          {{- range .paths }}
          - path: {{ .path }}
            pathType: {{ .pathType }}
            backend:
              service:
                name: {{ include "orthanc-oauth.fullname" $ }}
                port:
                  number: {{ $.Values.service.httpPort }}
          {{- end }}
    {{- end }}
{{- end }}
```

**Step 4: Validate all templates**

```bash
helm template test examples/kubernetes/orthanc-oauth/ --debug
helm lint examples/kubernetes/orthanc-oauth/ --strict
```

Expected: All templates valid, no errors

**Step 5: Commit**

```bash
git add examples/kubernetes/orthanc-oauth/templates/
git commit -m "feat(helm): add Service, HPA, and Ingress templates

Add Kubernetes resource templates:
- Service: ClusterIP with HTTP, DICOM, and metrics ports
- HorizontalPodAutoscaler: CPU and memory-based autoscaling
- Ingress: NGINX ingress with configurable hosts and TLS

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

### Task 8: Azure-Specific Values Override

**Files:**
- Create: `examples/kubernetes/orthanc-oauth/values-azure.yaml`

**Step 1: Create Azure values override**

File: `examples/kubernetes/orthanc-oauth/values-azure.yaml`
```yaml
# Azure-specific configuration overrides
# Use with: helm install orthanc . -f values-azure.yaml

# These values assume you have Azure resources already deployed:
# - Azure Health Data Services DICOM service
# - Azure Database for PostgreSQL Flexible Server
# - Azure Blob Storage account
# - Azure Key Vault (optional, for secrets)
# - User-Assigned Managed Identity with workload identity enabled

# Database configuration for Azure PostgreSQL
database:
  external:
    # Replace with your PostgreSQL server FQDN
    host: "REPLACE_WITH_POSTGRES_FQDN"  # e.g., myserver.postgres.database.azure.com
    port: 5432
    database: orthanc
    sslMode: require
    # Kubernetes secret should contain 'username' and 'password' keys
    # Create with: kubectl create secret generic azure-postgresql-creds \
    #   --from-literal=username=orthanc_admin \
    #   --from-literal=password=YOUR_PASSWORD
    credentialsSecret: azure-postgresql-creds

# Storage configuration for Azure Blob Storage
storage:
  external:
    provider: azure-blob
    # Kubernetes secret should contain 'connectionString' key
    # Create with: kubectl create secret generic azure-storage-creds \
    #   --from-literal=connectionString="DefaultEndpointsProtocol=https;AccountName=..."
    connectionStringSecret: azure-storage-creds
    container: orthanc-dicom

# OAuth plugin configuration for Azure DICOM service
oauthPlugin:
  logLevel: INFO
  rateLimitRequests: 100
  rateLimitWindowSeconds: 60

  servers:
    azure-dicom:
      # Replace with your DICOM service URL
      url: "REPLACE_WITH_DICOM_SERVICE_URL"  # e.g., https://workspace-dicom.dicom.azurehealthcareapis.com/v2/
      # Replace TENANT_ID with your Azure AD tenant ID
      tokenEndpoint: "https://login.microsoftonline.com/REPLACE_WITH_TENANT_ID/oauth2/v2.0/token"
      scope: "https://dicom.healthcareapis.azure.com/.default"
      tokenRefreshBufferSeconds: 300

      authentication:
        # Use Azure Workload Identity (recommended for AKS)
        type: workload-identity
        # Replace with your User-Assigned Managed Identity client ID
        clientId: "REPLACE_WITH_MANAGED_IDENTITY_CLIENT_ID"

# Service account with workload identity annotations
serviceAccount:
  create: true
  annotations:
    # Replace these with your actual values
    azure.workload.identity/client-id: "REPLACE_WITH_MANAGED_IDENTITY_CLIENT_ID"
    azure.workload.identity/tenant-id: "REPLACE_WITH_TENANT_ID"

# Pod annotations for workload identity
podAnnotations:
  azure.workload.identity/use: "true"

# Ingress configuration (example for Azure Application Gateway)
ingress:
  enabled: true
  className: azure-application-gateway
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    appgw.ingress.kubernetes.io/backend-protocol: http
    appgw.ingress.kubernetes.io/ssl-redirect: "true"
  hosts:
    - host: orthanc.example.com  # Replace with your domain
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: orthanc-tls
      hosts:
        - orthanc.example.com

# Monitoring (Azure Monitor integration)
monitoring:
  enabled: true
  prometheus:
    enabled: true
    port: 9090
  serviceMonitor:
    enabled: true  # If using Prometheus Operator
    interval: 30s

# Resource configuration (adjust based on workload)
resources:
  requests:
    cpu: 2000m
    memory: 4Gi
  limits:
    cpu: 4000m
    memory: 8Gi

# Autoscaling configuration
autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
  targetMemoryUtilizationPercentage: 80

# Node affinity (optional - prefer specific node pools)
# affinity:
#   nodeAffinity:
#     preferredDuringSchedulingIgnoredDuringExecution:
#     - weight: 100
#       preference:
#         matchExpressions:
#         - key: workload
#           operator: In
#           values:
#           - medical-imaging
```

**Step 2: Validate Azure values**

```bash
helm template test examples/kubernetes/orthanc-oauth/ \
  -f examples/kubernetes/orthanc-oauth/values-azure.yaml \
  --debug
```

Expected: Templates render correctly with Azure values

**Step 3: Create template test with real-ish values**

```bash
# Test with mock values to ensure template renders
helm template test examples/kubernetes/orthanc-oauth/ \
  -f examples/kubernetes/orthanc-oauth/values-azure.yaml \
  --set database.external.host=test.postgres.database.azure.com \
  --set oauthPlugin.servers.azure-dicom.url=https://test.dicom.azurehealthcareapis.com/v2/ \
  --set oauthPlugin.servers.azure-dicom.tokenEndpoint=https://login.microsoftonline.com/12345/oauth2/v2.0/token \
  --set oauthPlugin.servers.azure-dicom.authentication.clientId=test-client-id \
  --set serviceAccount.annotations."azure\.workload\.identity/client-id"=test-client-id \
  --set serviceAccount.annotations."azure\.workload\.identity/tenant-id"=12345
```

Expected: Valid Kubernetes YAML output

**Step 4: Commit**

```bash
git add examples/kubernetes/orthanc-oauth/values-azure.yaml
git commit -m "feat(helm): add Azure-specific values override

Add values-azure.yaml with Azure-specific configuration:
- Azure PostgreSQL connection settings
- Azure Blob Storage configuration
- Azure DICOM service OAuth settings
- Workload Identity annotations
- Application Gateway ingress example

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Phase 3: Azure Quickstart Infrastructure

### Task 9: Quickstart Folder Structure and Dockerfile

**Files:**
- Create: `examples/azure/quickstart/Dockerfile`
- Create: `examples/azure/quickstart/.dockerignore`
- Create: `examples/azure/quickstart/README.md` (placeholder)

**Step 1: Create Dockerfile**

File: `examples/azure/quickstart/Dockerfile`
```dockerfile
FROM orthancteam/orthanc:24.12.1-full

# Install Python dependencies for OAuth plugin
RUN apt-get update && \
    apt-get install -y python3-pip && \
    pip3 install --no-cache-dir \
        requests==2.31.0 \
        PyJWT==2.8.0 \
        cryptography==41.0.7 \
        redis==5.0.1 \
        prometheus-client==0.19.0 && \
    rm -rf /var/lib/apt/lists/*

# Copy OAuth plugin from repository root
# Build context should be repository root
COPY src/ /etc/orthanc/plugins/

# Plugin will be loaded via ORTHANC__PLUGINS environment variable
ENV ORTHANC__PLUGINS='["/etc/orthanc/plugins/dicomweb_oauth_plugin.py"]'

# Expose Orthanc HTTP and DICOM ports
EXPOSE 8042 4242

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:8042/system || exit 1

# Run as non-root user
USER orthanc

CMD ["Orthanc", "/etc/orthanc/"]
```

**Step 2: Create .dockerignore**

File: `examples/azure/quickstart/.dockerignore`
```.gitignore
# .dockerignore
*.md
.git
.gitignore
tests/
docs/
examples/
.mypy_cache/
.pytest_cache/
__pycache__/
*.pyc
.venv/
venv/
.env
```

**Step 3: Create README placeholder**

File: `examples/azure/quickstart/README.md`
```markdown
# Azure Quickstart Deployment

Deploy Orthanc with OAuth plugin to Azure Container Apps with client credentials authentication.

## Overview

- **Platform**: Azure Container Apps
- **Authentication**: OAuth client credentials
- **Networking**: Public endpoints with firewall rules
- **Cost**: ~$66/month
- **Setup Time**: ~15 minutes

## Prerequisites

- Azure subscription
- Azure CLI 2.50+
- Docker (for building custom image)
- Contributor + User Access Administrator role

## Documentation

Full documentation coming soon.

## Quick Start

```bash
# 1. Create app registration
./scripts/setup-app-registration.sh

# 2. Configure parameters
cp parameters.json.template parameters.json
# Edit parameters.json with your values

# 3. Deploy
./scripts/deploy.sh --resource-group rg-orthanc-demo --location eastus

# 4. Test
./scripts/test-deployment.sh
```
```

**Step 4: Test Dockerfile syntax**

```bash
# Validate Dockerfile syntax (without building)
docker run --rm -i hadolint/hadolint < examples/azure/quickstart/Dockerfile
```

Expected: No critical errors (warnings about pinning versions are OK)

**Step 5: Commit**

```bash
git add examples/azure/quickstart/
git commit -m "feat(azure): add quickstart Dockerfile and structure

Add Azure quickstart deployment structure:
- Dockerfile extending orthancteam/orthanc:full with OAuth plugin
- .dockerignore for efficient builds
- README placeholder

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

**NOTE: This plan continues for many more tasks. Due to length constraints, I'll provide a summary of remaining tasks below and save the complete plan.**

## Remaining Tasks Summary

### Phase 3 (Continued): Azure Quickstart
- Task 10: Bicep parameters template
- Task 11: Main Bicep template (AVM modules integration)
- Task 12: Orthanc config module
- Task 13: Setup app registration script
- Task 14: Deploy script
- Task 15: Test deployment script
- Task 16: Cleanup script

### Phase 4: Azure Production (Container Apps)
- Tasks 17-23: Similar to quickstart but with VNet, private endpoints, managed identity

### Phase 5: Azure Production AKS
- Tasks 24-30: AKS cluster deployment, Helm integration, workload identity

### Phase 6: Documentation
- Tasks 31-35: Comprehensive READMEs, architecture diagrams, troubleshooting guides

### Phase 7: Testing and CI/CD
- Tasks 36-40: Test data, automated tests, GitHub Actions workflows

Would you like me to:
1. Continue writing all remaining tasks in detail?
2. Save this abbreviated version and you can expand it later?
3. Focus on specific phases you want detailed now?
