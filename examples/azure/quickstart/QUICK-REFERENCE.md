# Transparent OAuth - Quick Reference Card

## 🎯 Goal
Send DICOM from Orthanc to Azure DICOM using standard UI button with automatic OAuth.

## ✅ What You Need

### 1. Azure Resources
- Health Data Services Workspace
- DICOM Service
- Service Principal with "DICOM Data Owner" role

### 2. Credentials
```bash
OAUTH_CLIENT_ID="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
OAUTH_CLIENT_SECRET="your-secret-value"
OAUTH_TOKEN_ENDPOINT="https://login.microsoftonline.com/{tenant-id}/oauth2/v2.0/token"
DICOM_SERVICE_URL="https://{workspace}.dicom.azurehealthcareapis.com/v1"  # ⚠️ Must include /v1 or /v2
DICOM_SCOPE="https://dicom.healthcareapis.azure.com/.default"
```

## 📝 Orthanc Configuration

### orthanc.json
```json
{
  "DicomWeb": {
    "Enable": true,
    "Servers": {
      "azure-dicom": {
        "Url": "http://localhost:8042/oauth-dicom-web/servers/azure-dicom",
        "Username": "${ORTHANC_USERNAME}",
        "Password": "${ORTHANC_PASSWORD}",
        "HasDelete": false,
        "ChunkedTransfers": true
      }
    }
  },
  "DicomWebOAuth": {
    "ConfigVersion": "2.0",
    "LogLevel": "INFO",
    "Servers": {
      "azure-dicom": {
        "Url": "${DICOM_SERVICE_URL}",
        "TokenEndpoint": "${OAUTH_TOKEN_ENDPOINT}",
        "ClientId": "${OAUTH_CLIENT_ID}",
        "ClientSecret": "${OAUTH_CLIENT_SECRET}",
        "Scope": "${DICOM_SCOPE}",
        "TokenRefreshBufferSeconds": 300,
        "VerifySSL": true
      }
    }
  }
}
```

### Environment Variables
```bash
# Orthanc
ORTHANC_USERNAME="admin"
ORTHANC_PASSWORD="your-password"

# OAuth
OAUTH_CLIENT_ID="your-client-id"
OAUTH_CLIENT_SECRET="your-client-secret"
OAUTH_TOKEN_ENDPOINT="https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"

# Azure DICOM
DICOM_SERVICE_URL="https://{workspace}.dicom.azurehealthcareapis.com/v1"
DICOM_SCOPE="https://dicom.healthcareapis.azure.com/.default"
```

## 🚀 How To Use

### From Orthanc UI
1. Upload DICOM study to Orthanc
2. Select study in Orthanc Explorer 2
3. Click **"Send to DICOMWeb server"**
4. Select **"azure-dicom"** from dropdown
5. Click **Send**

**That's it!** OAuth happens automatically.

### From API
```bash
curl -X POST \
  -u admin:password \
  -H "Content-Type: application/json" \
  -d '{"Resources": ["study-uuid"]}' \
  https://orthanc-url/dicom-web/servers/azure-dicom/stow
```

## ✅ Verify It's Working

### 1. Check Plugin Status
```bash
curl -u admin:password https://orthanc-url/dicomweb-oauth/status
```

Expected response:
```json
{
  "status": "healthy",
  "token_managers": 1,
  "servers_configured": 1
}
```

### 2. Check Container Logs
Look for:
```
✅ Acquiring new token
✅ auth_success
✅ Token acquired and validated
✅ Forwarding multipart DICOM data
✅ Azure response status: 200
✅ Successfully sent X instances to Azure DICOM
```

### 3. On Second Upload (Same Study)
```
✅ 409 Client Error: Conflict
```
**409 = Success!** Study already exists in Azure.

## 🐛 Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| 404 Not Found | Missing `/v1` in URL | Add `/v1` or `/v2` to `DICOM_SERVICE_URL` |
| 401 Unauthorized (proxy) | Wrong Orthanc credentials | Check `Username`/`Password` in DICOMweb config |
| 401 Unauthorized (Azure) | OAuth failed | Verify client credentials and scope |
| ImagePullFailure | Wrong arch | Build with `--platform linux/amd64` |
| UI shows error but logs show success | Response parsing | Normal - check logs to confirm upload worked |

## 🏗️ Docker Build

**CRITICAL for Azure deployment from Mac:**
```bash
# Run from inside examples/azure/quickstart/
docker buildx build \
  --platform linux/amd64 \
  -f Dockerfile \
  -t registry/image:tag \
  --push .
```

## 📊 Success Indicators

### First Upload
- HTTP 200 OK
- "Successfully sent X instances"
- Data appears in Azure

### Duplicate Upload
- HTTP 409 Conflict
- "Study already exists"
- Proves OAuth is working!

## 🔗 Full Documentation

- **Setup Guide**: [TRANSPARENT-OAUTH-GUIDE.md](TRANSPARENT-OAUTH-GUIDE.md)
- **Deployment**: [DEPLOYMENT-GUIDE.md](DEPLOYMENT-GUIDE.md)
- **Main README**: [../../../README.md](../../../README.md)

## 🎓 Key Concepts

### Why This Works
1. DICOMweb plugin thinks it's sending to "remote" server
2. "Remote" server is actually localhost OAuth proxy
3. OAuth proxy adds Bearer token
4. Forwards to real Azure DICOM service

### Architecture
```
UI → DICOMweb Plugin → OAuth Proxy → Azure DICOM
                    (localhost)      (with token)
```

### Configuration Pattern
- **DICOMweb URL**: Points to local proxy
- **OAuth Config**: Has real Azure URL + credentials
- **Result**: Transparent OAuth for users

## ✨ Benefits

- ✅ No user training needed
- ✅ Standard Orthanc UI works
- ✅ Automatic token management
- ✅ Works with any OAuth2 provider
- ✅ No nginx sidecar needed
- ✅ Single container deployment

---

**That's all you need to know!** 🎉

For troubleshooting and advanced configuration, see the full [Transparent OAuth Guide](TRANSPARENT-OAUTH-GUIDE.md).
