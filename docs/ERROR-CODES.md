# Error Codes Reference

All errors include structured error codes with troubleshooting steps.

## Error Categories

- **CONFIGURATION** (CFG-xxx): Configuration errors
- **AUTHENTICATION** (TOK-xxx): Token acquisition errors
- **NETWORK** (NET-xxx): Network connectivity errors
- **AUTHORIZATION** (AUTH-xxx): Authorization errors
- **INTERNAL** (INT-xxx): Internal plugin errors

## Configuration Errors

### CFG-001: CONFIG_MISSING_KEY
Required configuration key is missing.

**Troubleshooting:**
1. Check that all required keys are present in DicomWebOAuth.Servers config
2. Required keys: Url, TokenEndpoint, ClientId, ClientSecret
3. Verify configuration file syntax is valid JSON

### CFG-002: CONFIG_INVALID_VALUE
Configuration value is invalid.

**Troubleshooting:**
1. Verify that URLs are properly formatted (must start with http:// or https://)
2. Check that numeric values are within valid ranges
3. Ensure boolean values are true/false

### CFG-003: CONFIG_ENV_VAR_MISSING
Referenced environment variable is not set.

**Troubleshooting:**
1. Set the missing environment variable before starting Orthanc
2. Example: `export VAR_NAME=value`
3. For Docker: use `-e VAR_NAME=value` or env_file

## Token Acquisition Errors

### TOK-001: TOKEN_ACQUISITION_FAILED
Failed to acquire OAuth2 token.

**Troubleshooting:**
1. Verify ClientId and ClientSecret are correct
2. Check that token endpoint URL is accessible
3. Ensure OAuth2 client has required permissions/grants
4. Review Orthanc logs for detailed error from provider

### TOK-002: TOKEN_EXPIRED
Cached token has expired.

**Troubleshooting:**
1. Token will be automatically refreshed on next request
2. If problem persists, check token endpoint availability

### TOK-004: TOKEN_VALIDATION_FAILED
Token validation failed.

**Troubleshooting:**
1. Verify token signature and claims are valid
2. Check that token hasn't been tampered with
3. Ensure provider's public keys are accessible

### TOK-005: TOKEN_INVALID_RESPONSE
Invalid response from token endpoint.

**Troubleshooting:**
1. Check that token endpoint returned valid JSON
2. Verify response contains required 'access_token' field
3. Review provider documentation for response format

### TOK-006: TOKEN_REFRESH_FAILED
Failed to refresh OAuth2 token.

**Troubleshooting:**
1. Verify refresh token is still valid
2. Check that OAuth2 client supports refresh grants
3. Ensure refresh token hasn't been revoked

## Network Errors

### NET-001: NETWORK_TIMEOUT
Network timeout connecting to endpoint.

**Troubleshooting:**
1. Check network connectivity to the token endpoint
2. Verify firewall rules allow outbound HTTPS
3. Increase timeout if endpoint is known to be slow
4. Check if endpoint is experiencing downtime

### NET-002: NETWORK_CONNECTION_ERROR
Cannot establish connection to endpoint.

**Troubleshooting:**
1. Verify the endpoint URL is correct and accessible
2. Check DNS resolution for the endpoint hostname
3. Ensure no proxy is blocking the connection
4. Verify SSL/TLS certificates if using HTTPS

### NET-003: NETWORK_SSL_ERROR
SSL/TLS certificate verification failed.

**Troubleshooting:**
1. Verify the endpoint has a valid SSL certificate
2. Check certificate expiration date
3. For self-signed certs, set VerifySSL: false (not recommended for production)
4. Ensure system CA certificates are up to date

## Authorization Errors

### AUTH-001: AUTH_INVALID_CREDENTIALS
Invalid client credentials.

**Troubleshooting:**
1. Verify ClientId matches the registered OAuth2 client
2. Verify ClientSecret is correct and not expired
3. Check if credentials need to be rotated
4. Ensure OAuth2 client is not disabled

### AUTH-002: AUTH_INSUFFICIENT_SCOPE
Insufficient scope for requested operation.

**Troubleshooting:**
1. Add required scope to configuration Scope field
2. Verify OAuth2 client has permission for requested scope
3. Check DICOMweb server required scopes

### AUTH-003: AUTH_PROVIDER_UNAVAILABLE
Authentication provider is unavailable.

**Troubleshooting:**
1. Check if OAuth provider is experiencing an outage
2. Verify network connectivity to provider
3. Check provider status page if available
4. Consider implementing fallback authentication

## Error Response Format

```json
{
  "error_code": "TOK-001",
  "category": "AUTHENTICATION",
  "severity": "ERROR",
  "message": "Failed to acquire OAuth2 token",
  "details": {
    "server": "my-server",
    "endpoint": "https://auth.example.com/token"
  },
  "troubleshooting": [
    "Verify ClientId and ClientSecret are correct",
    "Check that token endpoint URL is accessible"
  ],
  "documentation_url": "https://github.com/rhavekost/orthanc-dicomweb-oauth/blob/main/docs/TROUBLESHOOTING.md#token-acquisition-failures",
  "http_status": 401
}
```
