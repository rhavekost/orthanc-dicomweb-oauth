# Orthanc OAuth Azure Quickstart - Deployment Guide

This deployment creates a complete Orthanc DICOM server with **transparent OAuth authentication** connected to Azure Health Data Services DICOM service.

> 📘 **Transparent OAuth Integration** - Users send DICOM studies to Azure using the standard Orthanc UI "Send to DICOMWeb server" button. OAuth authentication happens automatically in the background. See [TRANSPARENT-OAUTH-GUIDE.md](TRANSPARENT-OAUTH-GUIDE.md) for details.

## 🎯 What This Deploys

### Healthcare Services
- **Azure Health Data Services Workspace**
- **DICOM Service** (for cloud-native DICOM storage)
- **RBAC Permissions** (DICOM Data Owner role for the app registration)

### Orthanc Infrastructure
- **Container App** running Orthanc with OAuth plugin
- **PostgreSQL Flexible Server** for Orthanc metadata
- **Storage Account** with Azure Blob Storage for DICOM files
- **Log Analytics Workspace** for monitoring

### OAuth Integration
- **Service Principal** with DICOM Data Owner permissions
- **Client Credentials Flow** configured in Orthanc
- **Token Management** via the dicomweb-oauth plugin

## ⚙️ PostgreSQL Configuration

The deployment automatically configures PostgreSQL for Orthanc compatibility:

### Required Extensions
- `pg_trgm` - Text search for DICOM metadata queries
- `uuid-ossp` - UUID generation for database records

### SSL Configuration
- `require_secure_transport: off` - Disabled for simplified connectivity
- For production, consider enabling SSL with proper certificate configuration

### Orthanc Plugin Settings
Critical settings in `orthanc.json`:
- `Port: 5432` - **Hardcoded integer** (not environment variable)
- `EnableSSL: false` - Matches Azure PostgreSQL SSL setting
- Extensions are enabled via Bicep during deployment

**Why these matter:**
- Orthanc PostgreSQL plugin expects `Port` as integer, not string
- `EnableSSL` must use capital letters (not `EnableSsl`)
- Missing extensions cause silent connection failures

## 📋 Prerequisites

1. **Azure CLI** logged in
   ```bash
   az login
   ```

2. **Docker Desktop** running (required for building the image)

3. **App Registration** created with client secret
   - File: `app-registration.json` (already exists)
   - Contains: clientId, clientSecret, servicePrincipalObjectId

4. **Azure Container Registry** with the Orthanc OAuth image
   - Registry: `kostlabsacr.azurecr.io`

## 🚀 Deployment Options

### Option 1: Fresh Deployment (Recommended)

**When to use:**
- First time deploying
- You want a clean, consistent deployment
- Location or configuration changes

**Steps:**
```bash
# 1. Delete the existing resource group (if it exists)
az group delete --name rg-orthanc-quickstart --yes --no-wait

# 2. Wait for deletion to complete (check portal or run)
az group show --name rg-orthanc-quickstart
# Should return "ResourceGroupNotFound"

# 3. Run the deployment script
cd examples/azure/quickstart
./deploy.sh
```

### Option 2: Update Existing Deployment

**When to use:**
- Adding healthcare workspace to existing infrastructure
- Minor configuration changes

**Steps:**
```bash
cd examples/azure/quickstart
./deploy.sh
```

**Note:** The deployment is idempotent and will add missing resources.

## 🔧 What The Deployment Does

### Step 1: Validation
- Checks Azure CLI login
- Verifies Docker is running
- Validates configuration files exist

### Step 2: Docker Build
- Builds Orthanc image with OAuth plugin
- **CRITICAL:** Uses `--platform linux/amd64` for Azure compatibility
- Pushes to Azure Container Registry

### Step 3: Infrastructure Deployment
Creates resources via Bicep templates:

1. **Healthcare Workspace** (`healthcare-workspace.bicep`)
   - Workspace with unique name
   - DICOM service
   - CORS configuration
   - Authentication settings

2. **RBAC Assignment** (`dicom-rbac.bicep`)
   - Assigns "DICOM Data Owner" role
   - Grants service principal access to DICOM service

3. **Container App** (`main.bicep`)
   - Deploys Orthanc with all environment variables
   - Connects to PostgreSQL, Blob Storage, and DICOM service
   - Configures OAuth client credentials flow

### Step 4: Results
Outputs deployment information:
- Orthanc URL and credentials
- DICOM service URL and scope
- OAuth configuration details

## 🔑 Environment Variables

The Container App receives these environment variables (populated in orthanc.json):

```bash
# Database
ORTHANC__POSTGRESQL__HOST=<postgres-server>.postgres.database.azure.com
ORTHANC__POSTGRESQL__PORT=5432
ORTHANC__POSTGRESQL__DATABASE=orthanc
ORTHANC__POSTGRESQL__USERNAME=orthanc_admin
ORTHANC__POSTGRESQL__PASSWORD=<from-secret>

# Storage
ORTHANC__AZURE_BLOB_STORAGE__CONNECTION_STRING=<from-secret>
ORTHANC__AZURE_BLOB_STORAGE__CONTAINER=orthanc-dicom

# OAuth Configuration
OAUTH_CLIENT_ID=<from-app-registration>
OAUTH_CLIENT_SECRET=<from-secret>
OAUTH_TOKEN_ENDPOINT=https://login.microsoftonline.com/<tenant>/oauth2/v2.0/token

# DICOM Service
DICOM_SERVICE_URL=<from-healthcare-workspace>
DICOM_SCOPE=https://dicom.healthcareapis.azure.com/.default

# Orthanc Credentials
ORTHANC_USERNAME=admin
ORTHANC_PASSWORD=<from-secret>
```

## 🧪 Testing The OAuth Connection

After deployment:

1. **Access Orthanc**
   ```
   URL: https://orthanc-quickstart-app.<region>.azurecontainerapps.io
   Username: admin
   Password: <from deployment output>
   ```

2. **Test DICOMweb Connection**
   - Navigate to "DICOMweb Servers"
   - Find "azure-dicom" server
   - Click "Test Connection"
   - Should see: ✅ "Connection successful"

3. **Upload Test DICOM**
   - Upload a DICOM file to Orthanc
   - Go to DICOMweb Servers → azure-dicom
   - Click "Send Studies"
   - Select your study
   - Click "Send"
   - Should upload to Azure DICOM service using OAuth

4. **Verify in Azure Portal**
   - Go to Healthcare Workspace
   - Open DICOM Service
   - Click "DICOM Studies"
   - Should see your uploaded study

## 📁 Files Overview

```
examples/azure/quickstart/
├── main.bicep                      # Main deployment (subscription scope)
├── modules/
│   ├── healthcare-workspace.bicep  # Healthcare workspace + DICOM service
│   ├── dicom-rbac.bicep           # RBAC role assignments
│   └── orthanc-config.bicep       # (if exists)
├── deploy.sh                       # Deployment orchestration script
├── deployment-params.json          # Configuration parameters
├── app-registration.json           # OAuth app registration details
├── orthanc.json                    # Orthanc configuration template
└── DEPLOYMENT-GUIDE.md            # This file
```

## ⚠️ Common Issues

### 1. ImagePullBackOff / Image not found
**Cause:** Docker image built for wrong architecture (arm64 instead of amd64)
**Solution:** The deploy.sh script uses `--platform linux/amd64` automatically

### 2. RBAC Permission Denied
**Cause:** Role assignment hasn't propagated
**Solution:** Wait 5-10 minutes for Azure AD to propagate permissions

### 3. DICOM Connection Fails with 401
**Cause:**
- Client secret expired
- Service principal not assigned to DICOM service
**Solution:**
- Check app-registration.json has valid secret
- Verify RBAC assignment in Azure Portal

### 4. Health Probe Failures
**Already handled:** Health probes removed (Orthanc requires authentication)

## 🔄 Updating The Deployment

### Change Docker Image
1. Make code changes
2. Run `./deploy.sh` (rebuilds and redeploys)

### Change Configuration
1. Edit `deployment-params.json`
2. Run `./deploy.sh`

### Update DICOM Scope
Already configured in main.bicep as:
```
https://dicom.healthcareapis.azure.com/.default
```

## 📊 Monitoring

View logs:
```bash
# Container App logs
az containerapp logs show \
  --name orthanc-quickstart-app \
  --resource-group rg-orthanc-quickstart \
  --follow

# Log Analytics
az monitor log-analytics query \
  --workspace <workspace-id> \
  --analytics-query "ContainerAppConsoleLogs_CL | where ContainerName_s == 'orthanc' | order by TimeGenerated desc"
```

## 🧹 Cleanup

Delete everything:
```bash
az group delete --name rg-orthanc-quickstart --yes
```

## 📝 Next Steps After Deployment

1. ✅ Test OAuth connection to DICOM service
2. ✅ Upload sample DICOM studies
3. ✅ Verify studies appear in Azure Health Data Services
4. 📖 Review Orthanc logs for OAuth token requests
5. 🔒 Consider adding VNet integration (production)
6. 🔐 Rotate client secrets (90-day expiry recommended)
