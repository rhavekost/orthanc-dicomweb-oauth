# OAuth Provider Support

This plugin supports multiple OAuth2 providers through both specialized provider classes and a generic OAuth2 implementation.

## Provider Comparison

| Provider | Status | Provider Type | Auto-detection | Configuration Complexity |
|----------|--------|---------------|----------------|-------------------------|
| **Azure Entra ID** | ✅ Fully supported | `azure` (specialized) | ✅ Yes | Low |
| **Google Cloud Healthcare API** | ✅ Fully supported | `google` (specialized) | ✅ Yes | Low |
| **AWS HealthImaging** | ⚠️ Basic support | `aws` (specialized) | ✅ Yes | Medium |
| **Keycloak** | ✅ Supported | `generic` | ✅ Yes | Low |
| **Auth0** | ✅ Supported | `generic` | ❌ No | Low |
| **Okta** | ✅ Supported | `generic` | ❌ No | Low |
| **Other OAuth2** | ✅ Supported | `generic` | ❌ No | Varies |

## When to Use Specialized vs Generic Provider

**Use specialized provider when:**
- Your provider is in the list above (Azure, Google, AWS)
- You want provider-specific error messages
- You want automatic token endpoint configuration
- Auto-detection will work based on token endpoint URL

**Use generic provider when:**
- Your provider isn't listed above
- You have custom OAuth2 requirements
- You want maximum control over configuration
- You're using a custom OAuth2 server

---

## Azure Entra ID (formerly Azure AD)

**Class:** `AzureProvider`

**Recommended for:** Azure Health Data Services, Azure API for FHIR

**Configuration:**

```json
{
  "ProviderType": "azure",
  "TokenEndpoint": "https://login.microsoftonline.com/{tenant-id}/oauth2/v2.0/token",
  "ClientId": "${AZURE_CLIENT_ID}",
  "ClientSecret": "${AZURE_CLIENT_SECRET}",
  "Scope": "https://dicom.healthcareapis.azure.com/.default"
}
```

**Setup Steps:**

1. **Register App in Azure Portal:**
   - Go to Azure Portal → Entra ID → App registrations → New registration
   - Name: "Orthanc DICOMweb OAuth Plugin"
   - Redirect URI: Not needed for client credentials flow

2. **Create Client Secret:**
   - In your app registration → Certificates & secrets → New client secret
   - Copy the secret value immediately (it's only shown once)

3. **Grant Permissions:**
   - In your app registration → API permissions → Add a permission
   - Select "APIs my organization uses" → Find your Azure Health Data Services
   - Select "Application permissions" → Check required permissions
   - Click "Grant admin consent"

4. **Configure Plugin:**
   - Use the format shown above
   - Replace `{tenant-id}` with your tenant GUID
   - Set `AZURE_CLIENT_ID` and `AZURE_CLIENT_SECRET` environment variables

**Quick Start:** [Azure Quick Start Guide](quickstart-azure.md)

---

## Google Cloud Healthcare API

**Class:** `GoogleProvider`

**Recommended for:** Google Cloud Healthcare API DICOM stores

**Configuration:**

```json
{
  "ProviderType": "google",
  "TokenEndpoint": "https://oauth2.googleapis.com/token",
  "ClientId": "${GOOGLE_CLIENT_ID}",
  "ClientSecret": "${GOOGLE_CLIENT_SECRET}",
  "Scope": "https://www.googleapis.com/auth/cloud-healthcare"
}
```

**Setup Steps:**

1. **Create Service Account:**
   - Go to Google Cloud Console → IAM & Admin → Service Accounts
   - Click "Create Service Account"
   - Name: "orthanc-dicomweb-oauth"
   - Grant role: "Healthcare DICOM Editor" or "Healthcare DICOM Viewer"

2. **Create Service Account Key:**
   - Click on your service account → Keys → Add Key → Create new key
   - Choose JSON format
   - Download the key file

3. **Extract Credentials:**
   - Open the JSON key file
   - Use `client_id` and `private_key` values in configuration
   - For private_key, you may need to convert it to client credentials format

4. **Configure Plugin:**
   - Use the format shown above
   - Set `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` environment variables

**Quick Start:** [Google Quick Start Guide](quickstart-google.md)

---

## AWS HealthImaging

**Class:** `AWSProvider`

**Status:** ⚠️ Basic implementation - AWS uses Signature Version 4, not traditional OAuth2

**Configuration:**

```json
{
  "ProviderType": "aws",
  "TokenEndpoint": "https://sts.amazonaws.com/",
  "ClientId": "${AWS_ACCESS_KEY_ID}",
  "ClientSecret": "${AWS_SECRET_ACCESS_KEY}",
  "Region": "us-west-2"
}
```

**Note:** Full AWS Signature v4 implementation is pending. Current implementation provides basic credential management.

---

## Keycloak

**Class:** `GenericProvider`

**Configuration:**

```json
{
  "ProviderType": "generic",
  "TokenEndpoint": "https://keycloak.example.com/realms/healthcare/protocol/openid-connect/token",
  "ClientId": "${KEYCLOAK_CLIENT_ID}",
  "ClientSecret": "${KEYCLOAK_CLIENT_SECRET}",
  "Scope": "dicomweb-api"
}
```

**Quick Start:** [Keycloak Quick Start Guide](quickstart-keycloak.md)

---

## Auth0

**Class:** `GenericProvider`

**Configuration:**

```json
{
  "ProviderType": "generic",
  "TokenEndpoint": "https://your-tenant.auth0.com/oauth/token",
  "ClientId": "${AUTH0_CLIENT_ID}",
  "ClientSecret": "${AUTH0_CLIENT_SECRET}",
  "Scope": "read:dicom",
  "Audience": "https://dicom-api.example.com"
}
```

**Note:** Auth0 requires the `audience` parameter for client credentials.

---

## Okta

**Class:** `GenericProvider`

**Configuration:**

```json
{
  "ProviderType": "generic",
  "TokenEndpoint": "https://your-domain.okta.com/oauth2/default/v1/token",
  "ClientId": "${OKTA_CLIENT_ID}",
  "ClientSecret": "${OKTA_CLIENT_SECRET}",
  "Scope": "dicom:read dicom:write"
}
```

---

## Auto-Detection

Specialized providers are automatically detected by token endpoint URL:

```python
# Azure: Any URL containing "login.microsoftonline.com"
if "login.microsoftonline.com" in token_endpoint:
    provider = AzureProvider(config)

# Google: Any URL containing "googleapis.com"
if "googleapis.com" in token_endpoint or "google" in token_endpoint:
    provider = GoogleProvider(config)

# AWS: Region-specific endpoint or STS endpoint
if "amazonaws.com" in token_endpoint:
    provider = AWSProvider(config)

# Default: Generic OAuth2
provider = GenericProvider(config)
```

**Override auto-detection:**

```json
{
  "ProviderType": "generic",
  "TokenEndpoint": "https://login.microsoftonline.com/..."
}
```

## Provider Feature Comparison

| Feature | Azure | Google | AWS | Generic |
|---------|-------|--------|-----|---------|
| **Auto-detection** | ✅ | ✅ | ✅ | - |
| **JWT validation** | ✅ | ✅ | ✅ | ❌ |
| **Token refresh** | ✅ | ✅ | ✅ | ✅ |
| **Retry logic** | ✅ | ✅ | ✅ | ✅ |
| **Error messages** | Azure-specific | Google-specific | AWS-specific | Generic |
| **Setup complexity** | Low | Low | Medium | Low |
| **Dependencies** | None extra | None extra | boto3 | None |

## Troubleshooting by Provider

### Azure

**Common Issues:**
- **"Invalid scope"**: Use `{resource}/.default` format, not just scope name
- **"Tenant not found"**: Check tenant ID in token endpoint URL
- **"Invalid client"**: Verify client ID/secret in Azure Portal → App registrations

### Google

**Common Issues:**
- **"Invalid scope"**: Use full scope URL (e.g., `https://www.googleapis.com/auth/cloud-healthcare`)
- **"Invalid grant"**: Service account needs Cloud Healthcare API permissions
- **"Token expired"**: Check system clock (JWT validation is time-sensitive)

### AWS

**Common Issues:**
- **"Signature does not match"**: Check access key and secret
- **"Region mismatch"**: Specify correct region in configuration
- **"Access denied"**: IAM policy needs `medical-imaging:*` permissions

### Generic Providers

**Common Issues:**
- **"Invalid client"**: Check client ID/secret exactly as shown in provider
- **"Unsupported grant type"**: Verify provider supports client credentials flow
- **"Invalid scope"**: Check provider documentation for exact scope format

## Testing Your Provider

Test token acquisition:

```bash
curl -X POST http://localhost:8042/dicomweb-oauth/test
```

Expected response:
```json
{
  "token_acquired": true,
  "provider": "azure",
  "expires_in": 3600
}
```

## Adding a New Provider

See [CONTRIBUTING.md](../CONTRIBUTING.md#adding-a-new-provider) for how to create a specialized provider class.
