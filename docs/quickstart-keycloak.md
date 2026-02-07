# Quick Start: Keycloak/OIDC

This guide shows how to connect Orthanc to a DICOMweb server protected by Keycloak or any OIDC provider.

## Prerequisites

- Keycloak instance (or other OIDC provider)
- DICOMweb server configured to validate Keycloak JWT tokens
- Admin access to create Keycloak clients

## Step 1: Create Keycloak Client

1. Log into Keycloak Admin Console
2. Select your realm (e.g., `healthcare`)
3. Navigate to **Clients** → **Create Client**

**Client Settings:**
- **Client ID**: `orthanc-client`
- **Client Protocol**: `openid-connect`
- **Access Type**: `confidential`
- **Service Accounts Enabled**: `ON`
- **Valid Redirect URIs**: `*` (or specific URLs)
- **Direct Access Grants**: `ON`

4. Go to **Credentials** tab
5. Copy the **Client Secret**

## Step 2: Configure Client Scopes (Optional)

If your DICOMweb server requires specific scopes:

1. Go to **Client Scopes**
2. Create custom scope: `dicomweb`
3. Add mappers for required claims
4. Assign scope to your client

## Step 3: Configure Orthanc

Add to `orthanc.json`:

```json
{
  "Plugins": [
    "/etc/orthanc/plugins/dicomweb_oauth_plugin.py"
  ],

  "DicomWebOAuth": {
    "Servers": {
      "keycloak-dicom": {
        "Url": "https://dicom.example.com/dicom-web/",
        "TokenEndpoint": "https://keycloak.example.com/realms/healthcare/protocol/openid-connect/token",
        "ClientId": "${KEYCLOAK_CLIENT_ID}",
        "ClientSecret": "${KEYCLOAK_CLIENT_SECRET}",
        "Scope": "dicomweb",
        "TokenRefreshBufferSeconds": 300
      }
    }
  }
}
```

## Step 4: Set Environment Variables

```bash
export KEYCLOAK_CLIENT_ID="orthanc-client"
export KEYCLOAK_CLIENT_SECRET="your-keycloak-secret"
```

Or create `.env` file:
```
KEYCLOAK_CLIENT_ID=orthanc-client
KEYCLOAK_CLIENT_SECRET=your-keycloak-secret
```

## Step 5: Test Connection

```bash
# Check plugin status
curl http://localhost:8042/dicomweb-oauth/status

# Test token acquisition
curl -X POST http://localhost:8042/dicomweb-oauth/servers/keycloak-dicom/test

# Query DICOM studies
curl http://localhost:8042/dicom-web/studies
```

## Keycloak Token Endpoints

Common Keycloak token endpoint formats:

- **Keycloak 18+**: `https://keycloak.example.com/realms/{realm}/protocol/openid-connect/token`
- **Keycloak <18**: `https://keycloak.example.com/auth/realms/{realm}/protocol/openid-connect/token`

Replace `{realm}` with your realm name (e.g., `healthcare`, `master`).

## Other OIDC Providers

This plugin works with any OIDC-compliant provider:

### Auth0
```json
{
  "TokenEndpoint": "https://your-tenant.auth0.com/oauth/token",
  "ClientId": "${AUTH0_CLIENT_ID}",
  "ClientSecret": "${AUTH0_CLIENT_SECRET}",
  "Scope": "openid profile dicomweb",
  "Audience": "https://dicom.example.com"
}
```

### Okta
```json
{
  "TokenEndpoint": "https://your-domain.okta.com/oauth2/default/v1/token",
  "ClientId": "${OKTA_CLIENT_ID}",
  "ClientSecret": "${OKTA_CLIENT_SECRET}",
  "Scope": "dicomweb"
}
```

### Google Cloud Identity Platform
```json
{
  "TokenEndpoint": "https://oauth2.googleapis.com/token",
  "ClientId": "${GOOGLE_CLIENT_ID}",
  "ClientSecret": "${GOOGLE_CLIENT_SECRET}",
  "Scope": "https://www.googleapis.com/auth/cloud-healthcare"
}
```

## Troubleshooting

### Error: "invalid_client"

- Verify client ID matches exactly
- Check client secret is correct
- Ensure client is enabled in Keycloak
- Verify realm name in token endpoint

### Error: "unauthorized_client"

- Enable "Service Accounts" for the client
- Enable "Direct Access Grants"
- Check client has required scopes

### Error: "invalid_scope"

- Verify scope name matches Keycloak configuration
- Check scope is assigned to client
- Try without scope parameter (use empty string `""`)

### Token Not Accepted by DICOMweb Server

- Verify DICOMweb server is configured to validate Keycloak tokens
- Check token contains required claims (sub, aud, iss)
- Verify DICOMweb server has Keycloak public key/JWKS URL configured
- Check token format (JWT expected)

## Security Best Practices

1. **Use confidential clients** (not public)
2. **Rotate client secrets** regularly
3. **Use specific scopes** (not `*` or `openid` alone)
4. **Enable token revocation** in Keycloak
5. **Monitor token usage** via Keycloak events
6. **Use short token lifetimes** (15-60 minutes)
7. **Enable token refresh** for long-running connections

## Advanced Configuration

### Custom Token Lifetime

In Keycloak client settings:
- **Access Token Lifespan**: 15 minutes (recommended)
- **Refresh Token Lifespan**: 30 minutes
- Adjust `TokenRefreshBufferSeconds` accordingly

### Multiple Realms

Configure multiple servers for different realms:

```json
{
  "DicomWebOAuth": {
    "Servers": {
      "production-dicom": {
        "Url": "https://prod-dicom.example.com/",
        "TokenEndpoint": "https://keycloak.example.com/realms/production/protocol/openid-connect/token",
        "ClientId": "${PROD_CLIENT_ID}",
        "ClientSecret": "${PROD_CLIENT_SECRET}"
      },
      "staging-dicom": {
        "Url": "https://staging-dicom.example.com/",
        "TokenEndpoint": "https://keycloak.example.com/realms/staging/protocol/openid-connect/token",
        "ClientId": "${STAGING_CLIENT_ID}",
        "ClientSecret": "${STAGING_CLIENT_SECRET}"
      }
    }
  }
}
```

## References

- [Keycloak Documentation](https://www.keycloak.org/documentation)
- [OAuth 2.0 Client Credentials](https://oauth.net/2/grant-types/client-credentials/)
- [OIDC Core Specification](https://openid.net/specs/openid-connect-core-1_0.html)
