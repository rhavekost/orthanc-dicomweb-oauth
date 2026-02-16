# Configuration Reference

Complete reference for configuring the DICOMweb OAuth plugin.

## Configuration Structure

The plugin configuration is added to Orthanc's `orthanc.json` file under the `DicomWebOAuth` key:

```json
{
  "Plugins": [
    "/etc/orthanc/plugins/dicomweb_oauth_plugin.py"
  ],

  "DicomWebOAuth": {
    "Servers": {
      "server-name-1": { /* server config */ },
      "server-name-2": { /* server config */ }
    }
  }
}
```

## Server Configuration

Each server under `Servers` represents a DICOMweb endpoint that requires OAuth2 authentication.

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `Url` | string | Base URL of the DICOMweb server (must match request URLs) |
| `TokenEndpoint` | string* | OAuth2 token endpoint URL for client credentials flow |
| `ClientId` | string* | OAuth2 client identifier |
| `ClientSecret` | string* | OAuth2 client secret |

*\* Not required when `ProviderType` is `"azuremanagedidentity"`. For managed identity, only `Url` and `Scope` are required.*

### Optional Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `Scope` | string | `""` | OAuth2 scope parameter (space-separated if multiple) |
| `ProviderType` | string | `"auto"` | Provider type (`auto`, `azure`, `google`, `aws`, `keycloak`, `generic`, `azuremanagedidentity`) |
| `TokenRefreshBufferSeconds` | integer | `300` | Seconds before expiry to trigger proactive refresh |
| `VerifySSL` | boolean/string | `true` | SSL/TLS certificate verification (true/false/path) |

## Configuration Examples

### Minimal Configuration

```json
{
  "DicomWebOAuth": {
    "Servers": {
      "my-server": {
        "Url": "https://dicom.example.com/",
        "TokenEndpoint": "https://auth.example.com/oauth2/token",
        "ClientId": "client123",
        "ClientSecret": "secret456"
      }
    }
  }
}
```

### Azure Managed Identity Configuration

For Azure deployments with managed identity (no client credentials needed):

```json
{
  "DicomWebOAuth": {
    "Servers": {
      "azure-dicom": {
        "Url": "https://workspace-dicom.dicom.azurehealthcareapis.com/v2/",
        "ProviderType": "azuremanagedidentity",
        "Scope": "https://dicom.healthcareapis.azure.com/.default",
        "VerifySSL": true
      }
    }
  }
}
```

Uses `DefaultAzureCredential` from the Azure Identity SDK. The managed identity of the Azure compute resource (Container App, VM, etc.) must have the appropriate RBAC role (e.g., "DICOM Data Owner") on the target service.

### Complete Configuration

```json
{
  "DicomWebOAuth": {
    "Servers": {
      "production-dicom": {
        "Url": "https://dicom.prod.example.com/v2/",
        "TokenEndpoint": "https://login.microsoftonline.com/tenant-id/oauth2/v2.0/token",
        "ClientId": "${PROD_CLIENT_ID}",
        "ClientSecret": "${PROD_CLIENT_SECRET}",
        "Scope": "https://dicom.prod.example.com/.default",
        "TokenRefreshBufferSeconds": 600
      },
      "staging-dicom": {
        "Url": "https://dicom.staging.example.com/v2/",
        "TokenEndpoint": "https://login.microsoftonline.com/tenant-id/oauth2/v2.0/token",
        "ClientId": "${STAGING_CLIENT_ID}",
        "ClientSecret": "${STAGING_CLIENT_SECRET}",
        "Scope": "https://dicom.staging.example.com/.default",
        "TokenRefreshBufferSeconds": 300
      }
    }
  }
}
```

## Environment Variable Substitution

The plugin supports environment variable substitution using `${VAR_NAME}` syntax:

```json
{
  "ClientId": "${OAUTH_CLIENT_ID}",
  "ClientSecret": "${OAUTH_CLIENT_SECRET}"
}
```

**Benefits:**
- Secure credential management
- Separate configuration from secrets
- Docker-friendly (.env file support)
- CI/CD pipeline integration

**Supported in:**
- All string configuration values
- Nested objects
- Array elements

**Example:**
```bash
# Set environment variables
export OAUTH_CLIENT_ID="my-client-id"
export OAUTH_CLIENT_SECRET="my-secret"
export DICOM_URL="https://dicom.example.com/v2/"

# Use in configuration
{
  "Url": "${DICOM_URL}",
  "ClientId": "${OAUTH_CLIENT_ID}",
  "ClientSecret": "${OAUTH_CLIENT_SECRET}"
}
```

## Configuration Field Details

### Url

**Type:** string
**Required:** Yes
**Format:** Must be valid HTTP/HTTPS URL

The base URL of the DICOMweb server. This is used to match outgoing requests - only requests starting with this URL will have OAuth tokens injected.

**Important:**
- Include trailing slash if DICOMweb server expects it
- Must match exactly how Orthanc makes requests
- Case-sensitive

**Examples:**
```json
"Url": "https://dicom.example.com/v2/"
"Url": "https://workspace-dicom.dicom.azurehealthcareapis.com/v2/"
"Url": "https://healthcare.googleapis.com/v1/projects/PROJECT/locations/LOCATION/datasets/DATASET/dicomStores/STORE/dicomWeb/"
```

### TokenEndpoint

**Type:** string
**Required:** Yes
**Format:** Must be valid HTTP/HTTPS URL

The OAuth2 token endpoint that accepts client credentials grant type.

**Common Formats:**
- Azure AD: `https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token`
- Keycloak: `https://keycloak.example.com/realms/{realm}/protocol/openid-connect/token`
- Auth0: `https://{tenant}.auth0.com/oauth/token`
- Okta: `https://{domain}.okta.com/oauth2/default/v1/token`

### ClientId

**Type:** string
**Required:** Yes

OAuth2 client identifier. This is the public identifier for your application.

**Finding Your Client ID:**
- Azure: Application (client) ID from App Registration
- Keycloak: Client ID from Clients section
- Auth0: Client ID from Application settings
- Okta: Client ID from Application settings

### ClientSecret

**Type:** string
**Required:** Yes
**Sensitive:** Yes - use environment variables

OAuth2 client secret. This is the sensitive credential used to authenticate your application.

**Security:**
- Never commit to version control
- Use environment variables: `${CLIENT_SECRET}`
- Rotate regularly (90-180 days)
- Store in secrets manager (Azure Key Vault, AWS Secrets Manager, etc.)

### Scope

**Type:** string
**Required:** No
**Default:** `""` (empty string)

OAuth2 scope parameter. Specifies what permissions/resources the token should have access to.

**Common Values:**
- Azure: `https://dicom.healthcareapis.azure.com/.default`
- Google Cloud: `https://www.googleapis.com/auth/cloud-healthcare`
- Custom: Space-separated list (e.g., `"dicomweb read write"`)
- Empty: `""` if scope not required

### TokenRefreshBufferSeconds

**Type:** integer
**Required:** No
**Default:** 300 (5 minutes)
**Range:** 0 - 3600

Number of seconds before token expiration to trigger proactive refresh.

**Recommendations:**
- Short-lived tokens (15 min): 120-300 seconds
- Medium tokens (1 hour): 300-600 seconds
- Long-lived tokens (1+ hour): 600-1800 seconds

**Example:**
```json
"TokenRefreshBufferSeconds": 600  // Refresh 10 minutes before expiry
```

### VerifySSL

**Type:** Boolean or String
**Default:** `true`
**Required:** No

Controls SSL/TLS certificate verification when connecting to the OAuth token endpoint.

**Options:**
- `true` (default): Verify SSL certificates using system CA bundle
- `false`: Disable SSL verification (⚠️ NOT RECOMMENDED for production)
- `"/path/to/ca-bundle.crt"`: Use custom CA certificate bundle

**Example:**
```json
{
  "DicomWebOAuth": {
    "Servers": {
      "production-server": {
        "VerifySSL": true
      },
      "dev-server-with-self-signed-cert": {
        "VerifySSL": "/etc/ssl/certs/company-ca.crt"
      }
    }
  }
}
```

**Security Warning:** Disabling SSL verification (`false`) makes connections vulnerable to man-in-the-middle attacks. Only use this for local development with self-signed certificates, and NEVER in production.

## Multiple Servers

Configure multiple DICOMweb servers with different OAuth providers:

```json
{
  "DicomWebOAuth": {
    "Servers": {
      "azure-prod": {
        "Url": "https://prod.dicom.azurehealthcareapis.com/v2/",
        "TokenEndpoint": "https://login.microsoftonline.com/tenant1/oauth2/v2.0/token",
        "ClientId": "${AZURE_PROD_CLIENT_ID}",
        "ClientSecret": "${AZURE_PROD_SECRET}",
        "Scope": "https://dicom.healthcareapis.azure.com/.default"
      },
      "keycloak-staging": {
        "Url": "https://staging.dicom.internal/dicom-web/",
        "TokenEndpoint": "https://keycloak.internal/realms/staging/protocol/openid-connect/token",
        "ClientId": "${KEYCLOAK_CLIENT_ID}",
        "ClientSecret": "${KEYCLOAK_SECRET}",
        "Scope": "dicomweb"
      },
      "google-research": {
        "Url": "https://healthcare.googleapis.com/v1/projects/my-project/locations/us-central1/datasets/research/dicomStores/images/dicomWeb/",
        "TokenEndpoint": "https://oauth2.googleapis.com/token",
        "ClientId": "${GOOGLE_CLIENT_ID}",
        "ClientSecret": "${GOOGLE_SECRET}",
        "Scope": "https://www.googleapis.com/auth/cloud-healthcare"
      }
    }
  }
}
```

## Configuration Validation

The plugin validates configuration on startup:

**Checked:**
- `DicomWebOAuth` section exists
- `Servers` section exists
- Each server has required fields
- URLs are valid format
- Environment variables are set

**On Error:**
- Plugin logs detailed error message
- Orthanc startup fails (safe failure)
- Check Orthanc logs for details

## Best Practices

1. **Use environment variables** for all secrets
2. **Descriptive server names** (e.g., `azure-prod-dicom`, `keycloak-staging`)
3. **Separate environments** (prod/staging/dev servers)
4. **Document scope requirements** in comments
5. **Test configuration** with monitoring endpoints
6. **Version control** orthanc.json (without secrets)
7. **Automate deployment** with CI/CD
8. **Monitor token usage** via plugin status endpoint

## Testing Configuration

After modifying configuration:

```bash
# 1. Restart Orthanc
docker-compose restart orthanc

# 2. Check plugin loaded
curl http://localhost:8042/dicomweb-oauth/status

# 3. List configured servers
curl http://localhost:8042/dicomweb-oauth/servers

# 4. Test each server
curl -X POST http://localhost:8042/dicomweb-oauth/servers/SERVER_NAME/test
```

## References

- [OAuth 2.0 RFC 6749](https://tools.ietf.org/html/rfc6749)
- [Client Credentials Grant](https://oauth.net/2/grant-types/client-credentials/)
- [Orthanc Plugin SDK](https://book.orthanc-server.com/plugins/python.html)
