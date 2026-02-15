# Truly Standalone Azure Deployment

This document describes the enhancements made to ensure the Orthanc OAuth Azure quickstart works on **brand new Azure subscriptions** without any external dependencies.

## 🎯 What Changed

### ✅ Now Truly Standalone

The deployment now creates **everything** within a single resource group, including:

1. **Azure Container Registry** (NEW!) - automatically created
2. **Healthcare Workspace + DICOM Service**
3. **PostgreSQL Flexible Server**
4. **Storage Account with Blob Storage**
5. **Container Apps Environment**
6. **Log Analytics Workspace**
7. **Container App with Orthanc**
8. **RBAC Permissions**

### ✅ Works on Brand New Subscriptions

The deployment now handles:

1. **Automatic Resource Provider Registration** - registers all required Azure resource providers
2. **No Pre-existing Infrastructure** - doesn't assume any resources exist
3. **Single Resource Group** - everything in one place for easy cleanup

### ✅ Cross-Platform Support

Both **Bash** and **PowerShell** scripts provided:

- **Bash scripts** (`deploy-new.sh`, `setup-app-registration.sh`) - Mac, Linux, Windows (WSL/Git Bash)
- **PowerShell scripts** (`Deploy.ps1`, `Setup-AppRegistration.ps1`) - Windows, Mac, Linux (PowerShell Core 7+)

---

## 📋 New File Structure

```
examples/azure/quickstart/
├── modules/
│   ├── container-registry.bicep         # NEW: ACR module
│   ├── healthcare-workspace.bicep
│   └── dicom-rbac.bicep
├── main.bicep                           # UPDATED: Creates ACR
├── deploy-new.sh                        # NEW: Standalone bash deployment
├── Deploy.ps1                           # NEW: PowerShell deployment
├── setup-app-registration.sh            # NEW: Bash app reg setup
├── Setup-AppRegistration.ps1            # NEW: PowerShell app reg setup
├── deployment-params-new.json           # NEW: Simplified parameters (no ACR)
├── deploy.sh                            # OLD: Requires existing ACR
└── deployment-params.json               # OLD: Includes ACR fields
```

---

## 🆕 Key Improvements

### 1. Self-Contained Container Registry

**Before:**
- Required pre-existing ACR (`kostlabsacr.azurecr.io`)
- Manual ACR setup before deployment
- Shared across deployments

**After:**
- ACR created automatically during deployment
- Unique ACR per deployment
- No manual setup required
- Everything in one resource group

**Implementation:**
```bicep
// modules/container-registry.bicep
resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: registryName
  location: location
  sku: { name: 'Basic' }
  properties: { adminUserEnabled: true }
}
```

### 2. Automatic Resource Provider Registration

**Before:**
- Assumed resource providers were registered
- Failed on brand new subscriptions

**After:**
- Automatically registers all required providers:
  - `Microsoft.ContainerRegistry`
  - `Microsoft.HealthcareApis`
  - `Microsoft.Storage`
  - `Microsoft.DBforPostgreSQL`
  - `Microsoft.App`
  - `Microsoft.OperationalInsights`

**Implementation (Bash):**
```bash
for provider in "${PROVIDERS[@]}"; do
    reg_state=$(az provider show --namespace "$provider" --query "registrationState" -o tsv)
    if [ "$reg_state" != "Registered" ]; then
        az provider register --namespace "$provider" --wait
    fi
done
```

### 3. Simplified Parameters

**Before (`deployment-params.json`):**
```json
{
  "containerImage": "kostlabsacr.azurecr.io/orthanc-oauth:latest",
  "containerRegistryName": "kostlabsacr",
  ...
}
```

**After (`deployment-params-new.json`):**
```json
{
  "environmentName": "quickstart",
  "location": "westus2",
  "resourceGroupName": "rg-orthanc-quickstart",
  ...
  // No ACR fields needed!
}
```

### 4. App Registration Automation

**Before:**
- Manual app registration creation
- Manual service principal setup
- Manual client secret generation

**After:**
- Automated scripts for both Bash and PowerShell
- One command creates everything
- Saves credentials to `app-registration.json`

**Usage:**
```bash
# Bash
./setup-app-registration.sh

# PowerShell
./Setup-AppRegistration.ps1
```

### 5. Two-Phase Deployment

To solve the chicken-and-egg problem (Container App needs image, but ACR doesn't exist yet):

**Phase 1: Infrastructure Deployment**
- Deploy ACR, Healthcare, Database, Storage, Container App Environment
- Container App created with correct image reference

**Phase 2: Image Build & Push**
- Get ACR credentials from deployed registry
- Build Docker image with `--platform linux/amd64`
- Push to the newly created ACR
- Container App pulls image on first start

---

## 🚀 How to Use

### Option 1: Bash (Mac, Linux, Windows with WSL)

```bash
# 1. Create app registration (one-time)
cd examples/azure/quickstart
./setup-app-registration.sh

# 2. Review/edit parameters
vi deployment-params-new.json

# 3. Deploy everything
./deploy-new.sh
```

### Option 2: PowerShell (Windows, Mac, Linux with PowerShell 7+)

```powershell
# 1. Create app registration (one-time)
cd examples/azure/quickstart
./Setup-AppRegistration.ps1

# 2. Review/edit parameters
notepad deployment-params-new.json

# 3. Deploy everything
./Deploy.ps1
```

---

## 🔍 Resource Provider Registration Details

### Why This Matters

Brand new Azure subscriptions don't have resource providers registered by default. Attempting to create resources without registration fails with errors like:

```
The subscription is not registered to use namespace 'Microsoft.HealthcareApis'
```

### What Gets Registered

| Provider | Used For | Registration Time |
|----------|----------|-------------------|
| `Microsoft.ContainerRegistry` | Azure Container Registry | ~1-2 minutes |
| `Microsoft.HealthcareApis` | Healthcare Workspace + DICOM | ~2-3 minutes |
| `Microsoft.Storage` | Storage Accounts | Usually pre-registered |
| `Microsoft.DBforPostgreSQL` | PostgreSQL Flexible Server | ~1-2 minutes |
| `Microsoft.App` | Container Apps | ~2-3 minutes |
| `Microsoft.OperationalInsights` | Log Analytics | ~1-2 minutes |

### Manual Registration (if needed)

```bash
az provider register --namespace Microsoft.HealthcareApis --wait
az provider register --namespace Microsoft.App --wait
# etc...
```

---

## 🔒 Security Considerations

### App Registration Secrets

The `app-registration.json` file contains sensitive credentials:

```json
{
  "tenantId": "...",
  "clientId": "...",
  "clientSecret": "SENSITIVE - DO NOT COMMIT",
  "servicePrincipalObjectId": "..."
}
```

**Best Practices:**
1. ✅ Add `app-registration.json` to `.gitignore`
2. ✅ Rotate client secrets every 90 days
3. ✅ Use Azure Key Vault for production
4. ✅ Use managed identities when possible

### Container Registry Access

The deployment uses ACR admin credentials for simplicity. For production:

```bash
# Option 1: Use managed identity (recommended)
az containerapp update \
  --name orthanc-quickstart-app \
  --resource-group rg-orthanc-quickstart \
  --registry-identity system

# Option 2: Use Azure RBAC
az role assignment create \
  --assignee <container-app-identity> \
  --role AcrPull \
  --scope <acr-resource-id>
```

---

## 📊 Cost Estimate

Approximate monthly cost for the quickstart deployment (West US 2):

| Resource | SKU | Monthly Cost (USD) |
|----------|-----|-------------------|
| Container Registry | Basic | $5 |
| Healthcare Workspace | Standard | $0 (workspace itself) |
| DICOM Service | Standard | $0.50/GB stored |
| PostgreSQL | Burstable B2s | $25 |
| Storage Account | Standard LRS | $0.02/GB |
| Container App | 1 vCPU, 2GB RAM | ~$30 |
| Log Analytics | Pay-as-you-go | $2-5 |

**Total: ~$60-70/month** (excluding DICOM storage)

---

## 🧹 Cleanup

Delete everything with a single command:

```bash
az group delete --name rg-orthanc-quickstart --yes
```

This removes:
- ✅ Container Registry + all images
- ✅ Healthcare Workspace + DICOM Service
- ✅ PostgreSQL Server + databases
- ✅ Storage Account + blob containers
- ✅ Container App + environment
- ✅ Log Analytics workspace
- ✅ All RBAC role assignments

---

## 🐛 Troubleshooting

### Issue: "Subscription not registered"

**Cause:** Resource provider not registered
**Solution:** Script handles this automatically, but if needed:
```bash
az provider register --namespace Microsoft.HealthcareApis --wait
```

### Issue: "ImagePullBackOff"

**Cause:** Image built for wrong architecture (arm64 instead of amd64)
**Solution:** Script uses `--platform linux/amd64` automatically

### Issue: "No such file or directory: docker"

**Cause:** Docker not installed or not in PATH
**Solution:**
- Install Docker Desktop
- Ensure `docker` command is available: `docker --version`

### Issue: PowerShell script won't run on Windows

**Cause:** Execution policy restriction
**Solution:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## 📝 Migration from Old Scripts

If you're using the old `deploy.sh`:

### 1. Update parameters file

```bash
# Remove these fields from deployment-params.json:
# - containerImage
# - containerRegistryName
```

### 2. Use new scripts

```bash
# Old way
./deploy.sh

# New way
./deploy-new.sh
```

### 3. Benefits of migration

- ✅ No pre-existing ACR needed
- ✅ Everything in one resource group
- ✅ Easier cleanup
- ✅ Works on brand new subscriptions

---

## 🎓 Learning Resources

- [Azure Container Apps Documentation](https://learn.microsoft.com/en-us/azure/container-apps/)
- [Azure Health Data Services](https://learn.microsoft.com/en-us/azure/healthcare-apis/)
- [Azure Container Registry](https://learn.microsoft.com/en-us/azure/container-registry/)
- [Resource Provider Registration](https://learn.microsoft.com/en-us/azure/azure-resource-manager/management/resource-providers-and-types)

---

## 🤝 Contributing

Found an issue or have a suggestion? Please open an issue with:
- Your operating system
- Azure subscription type (new/existing)
- Error messages (if any)
- Steps to reproduce
