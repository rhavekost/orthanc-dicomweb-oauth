# Azure Deployment Status - February 14, 2026

## Executive Summary

Azure infrastructure deployment is **95% complete**. All resources are provisioned and running, but there's a remaining connectivity issue preventing external access to the Orthanc API.

## ✅ Completed

### Infrastructure Deployed
- **Resource Group**: `rg-orthanc-quickstart` (Central US)
- **Healthcare Workspace**: `orthancws4352e8`
- **DICOM Service**: `orthancdicom` (https://orthancws4352e8-orthancdicom.dicom.azurehealthcareapis.com)
- **Container App**: `orthanc-quickstart-app` (running)
- **PostgreSQL**: `orthanc-quickstart-db-afjf274fdrr5w` (Burstable, 32GB)
- **Storage Account**: `orthancquickstartsaafjf2` (Blob storage)
- **App Registration**: OAuth client credentials configured

### Code Improvements
1. **Docker Image** (`examples/azure/quickstart/Dockerfile`):
   - Fixed Python 3.11+ pip install (PEP 668) with `--break-system-packages`
   - Fixed CMD to use config path only (not 'Orthanc' binary)
   - Removed USER directive (base image handles user switching)
   - Added orthanc.json configuration with RemoteAccessAllowed

2. **Bicep Templates**:
   - Fixed parameter format (wrapped in `{"value": "..."}`)
   - Added `containerRegistryPassword` parameter for ACR authentication
   - Disabled zone redundancy and high availability (quickstart mode)
   - Removed ACR role assignment (using admin credentials instead)
   - Fixed healthcare workspace module integration

3. **Deployment Scripts**:
   - Made idempotent (password reuse from deployment-details.json)
   - Fixed unbound variable errors
   - Added ACR credential retrieval
   - Region flexibility (switched from eastus to centralus due to quota)

4. **Test Data**:
   - Created synthetic DICOM generator (20 CT images)
   - Created upload script with auto-detection

## ❌ Remaining Issue

### Container App HTTP Timeout

**Symptoms**:
- Container logs show: "HTTP server listening on port: 8042 (remote access is allowed)" ✓
- DICOM server running on port 4242 ✓
- SSL/TLS handshake succeeds ✓
- HTTP requests timeout after 10+ seconds (no response)

**Investigation**:
- Container is running (1 replica healthy, 1 activating)
- Ingress configured: external=true, targetPort=8042, transport=Http
- Health check is localhost-only (might be causing issues)

**Possible Causes**:
1. **Authentication mismatch**: Static orthanc.json config vs environment variable auth
2. **Container Apps HTTP/2**: May need HTTP/1.1 transport instead
3. **Health probe failure**: Container restarting before accepting connections
4. **Network policy**: Container Apps private networking blocking public ingress

## 🔍 Debugging Steps to Try

### Option 1: Check Container App Logs
```bash
az containerapp logs show \
  --name orthanc-quickstart-app \
  --resource-group rg-orthanc-quickstart \
  --follow
```

### Option 2: Test from within Azure
Create a temporary VM in the same region and test connectivity from inside Azure network.

### Option 3: Simplify Configuration
Remove orthanc.json entirely and let environment variables handle all config:
```dockerfile
# Remove this line from Dockerfile:
COPY examples/azure/quickstart/orthanc.json /etc/orthanc/orthanc.json
```

### Option 4: Use Container Instances Instead
Deploy using Azure Container Instances (simpler, no ingress layer):
```bash
az container create \
  --resource-group rg-orthanc-quickstart \
  --name orthanc-oauth-test \
  --image kostlabsacr.azurecr.io/orthanc-oauth:latest \
  --dns-name-label orthanc-test \
  --ports 8042 \
  --cpu 2 --memory 4
```

## 📊 Current Credentials

**Orthanc**:
- URL: https://orthanc-quickstart-app.yellowmoss-5371d756.centralus.azurecontainerapps.io
- Username: `admin`
- Password: `KpG5Hq0jCAilc3Ywwi6622FMpeWJmfST`

**PostgreSQL**:
- Server: `orthanc-quickstart-db-afjf274fdrr5w.postgres.database.azure.com`
- Database: `orthanc`
- Username: `orthanc_admin`
- Password: (stored in `examples/azure/quickstart/scripts/deployment-details.json`)

**App Registration**:
- Client ID: (in `examples/azure/quickstart/app-registration.json`)
- Tenant ID: (in `examples/azure/quickstart/app-registration.json`)

## 🎯 Next Actions

### Immediate (to complete deployment):
1. [ ] Resolve Container App connectivity issue
2. [ ] Verify Orthanc API accessible
3. [ ] Upload synthetic DICOM test data
4. [ ] Test OAuth flow with Azure DICOM service
5. [ ] Grant DICOM Data Owner role to Container App managed identity

### Future Improvements:
1. [ ] Add VNet integration (production example)
2. [ ] Enable private endpoints for PostgreSQL and Storage
3. [ ] Add Application Insights monitoring
4. [ ] Create Helm charts as alternative deployment
5. [ ] Add automated testing in CI/CD

## 📝 Files Modified

### New Files:
- `examples/azure/quickstart/orthanc.json` - Orthanc server configuration
- `examples/azure/quickstart/modules/healthcare-workspace.bicep` - DICOM service module
- `examples/azure/test-data/generate-synthetic-dicom.py` - Test data generator
- `examples/azure/test-data/upload-test-data.sh` - Upload script

### Modified Files:
- `examples/azure/quickstart/Dockerfile` - Python 3.11+ and CMD fixes
- `examples/azure/quickstart/main.bicep` - ACR auth and HA fixes
- `examples/azure/quickstart/scripts/deploy.sh` - Idempotency and ACR credentials
- `examples/azure/production/scripts/deploy.sh` - Same idempotency fixes
- `.gitignore` - Added deployment artifact files

## 💾 Git Commits

```bash
0742954 fix(azure): improve Dockerfile and add Orthanc configuration
1d34029 feat(azure): add healthcare workspace module and deployment improvements
a2d863b feat(azure): make deployment scripts idempotent
```

All code pushed to: https://github.com/rhavekost/orthanc-dicomweb-oauth

## 🧪 Testing

Once connectivity is resolved:

```bash
# Test Orthanc API
curl -u admin:KpG5Hq0jCAilc3Ywwi6622FMpeWJmfST \
  https://orthanc-quickstart-app.yellowmoss-5371d756.centralus.azurecontainerapps.io/system

# Upload test data
cd examples/azure/test-data
./upload-test-data.sh \
  --deployment-dir ../quickstart/scripts \
  --url https://orthanc-quickstart-app.yellowmoss-5371d756.centralus.azurecontainerapps.io

# Verify data in Orthanc
curl -u admin:KpG5Hq0jCAilc3Ywwi6622FMpeWJmfST \
  https://orthanc-quickstart-app.yellowmoss-5371d756.centralus.azurecontainerapps.io/instances
```

## 📚 Resources

- [Azure Container Apps Documentation](https://learn.microsoft.com/en-us/azure/container-apps/)
- [Orthanc Configuration](https://orthanc.uclouvain.be/book/users/configuration.html)
- [Azure Health Data Services](https://learn.microsoft.com/en-us/azure/healthcare-apis/)
