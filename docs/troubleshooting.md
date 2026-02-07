# Troubleshooting Guide

Common issues and solutions for the DICOMweb OAuth plugin.

## Plugin Not Loading

### Symptom
Plugin doesn't appear in Orthanc logs or status endpoint returns 404.

### Solutions

1. **Check plugin path in orthanc.json:**
   ```json
   {
     "Plugins": [
       "/etc/orthanc/plugins/dicomweb_oauth_plugin.py"  // Verify this path
     ]
   }
   ```

2. **Verify Python files exist:**
   ```bash
   ls -la /etc/orthanc/plugins/
   # Should show: dicomweb_oauth_plugin.py, token_manager.py, config_parser.py
   ```

3. **Check Python version:**
   ```bash
   python3 --version  # Must be 3.8+
   ```

4. **Check Orthanc logs:**
   ```bash
   docker-compose logs orthanc | grep -i oauth
   ```

## Configuration Errors

### Error: "Missing 'DicomWebOAuth' section"

**Cause:** Configuration section not found in orthanc.json

**Solution:**
```json
{
  "DicomWebOAuth": {  // Add this section
    "Servers": { /* ... */ }
  }
}
```

### Error: "Environment variable 'VAR_NAME' referenced but not set"

**Cause:** Configuration uses `${VAR_NAME}` but environment variable doesn't exist

**Solutions:**

1. **Set environment variable:**
   ```bash
   export VAR_NAME="value"
   ```

2. **Use Docker .env file:**
   ```bash
   # docker/.env
   VAR_NAME=value
   ```

3. **Set in docker-compose.yml:**
   ```yaml
   environment:
     - VAR_NAME=value
   ```

### Error: "Server 'X' missing required config keys"

**Cause:** Required fields missing from server configuration

**Solution:** Ensure all required fields present:
```json
{
  "Url": "...",           // Required
  "TokenEndpoint": "...", // Required
  "ClientId": "...",      // Required
  "ClientSecret": "..."   // Required
}
```

## Token Acquisition Errors

### Error: "invalid_client"

**Causes:**
- Wrong client ID or secret
- Client doesn't exist
- Client is disabled

**Solutions:**

1. **Verify credentials:**
   ```bash
   # Test manually
   curl -X POST https://your-token-endpoint/token \
     -d "grant_type=client_credentials" \
     -d "client_id=YOUR_ID" \
     -d "client_secret=YOUR_SECRET"
   ```

2. **Check client status** in OAuth provider admin console
3. **Regenerate client secret** if expired
4. **Verify environment variables loaded:**
   ```bash
   docker-compose exec orthanc env | grep CLIENT
   ```

### Error: "unauthorized_client"

**Causes:**
- Client not authorized for client_credentials grant
- Client doesn't have required permissions

**Solutions (Keycloak):**
1. Client Settings → Enable "Service Accounts"
2. Client Settings → Enable "Direct Access Grants"

**Solutions (Azure):**
1. API Permissions → Add required permissions
2. Grant admin consent
3. Wait 5-10 minutes for propagation

### Error: "invalid_scope"

**Causes:**
- Scope doesn't exist
- Client not authorized for scope

**Solutions:**

1. **Remove scope** if not required:
   ```json
   {
     "Scope": ""  // Empty string
   }
   ```

2. **Verify scope format:**
   - Azure: `https://resource/.default`
   - Others: Space-separated list

3. **Check OAuth provider** for valid scopes

### Error: "Failed to acquire token... after 3 attempts"

**Causes:**
- Network connectivity issues
- Token endpoint unreachable
- Firewall blocking requests

**Solutions:**

1. **Test connectivity:**
   ```bash
   docker-compose exec orthanc curl -v https://your-token-endpoint
   ```

2. **Check DNS resolution:**
   ```bash
   docker-compose exec orthanc nslookup your-token-endpoint.com
   ```

3. **Review firewall rules**
4. **Check proxy settings** if behind corporate proxy

## Request Filtering Issues

### Issue: Authorization header not added

**Causes:**
- URL mismatch between configuration and requests
- Plugin not intercepting requests

**Debug:**

1. **Check configured URL:**
   ```bash
   curl http://localhost:8042/dicomweb-oauth/servers
   # Look at "url" field
   ```

2. **Verify URL matching:**
   - Configuration: `https://dicom.example.com/v2/`
   - Request must start with: `https://dicom.example.com/v2/`
   - Case-sensitive!
   - Trailing slash matters!

3. **Enable debug logging:**
   ```json
   {
     "Verbosity": "trace"
   }
   ```

4. **Check Orthanc logs:**
   ```bash
   docker-compose logs orthanc | grep "Injecting OAuth token"
   ```

### Issue: Wrong server matched

**Cause:** Multiple servers with overlapping URLs

**Solution:** Order servers from most specific to least specific

**Bad:**
```json
{
  "server1": { "Url": "https://dicom.example.com/" },
  "server2": { "Url": "https://dicom.example.com/v2/" }
}
```

**Good:**
```json
{
  "server2": { "Url": "https://dicom.example.com/v2/" },  // More specific first
  "server1": { "Url": "https://dicom.example.com/" }
}
```

## DICOMweb Connection Errors

### Error: 401 Unauthorized from DICOMweb server

**Causes:**
- Token not being added (see above)
- Token invalid/expired
- Server doesn't recognize token

**Debug:**

1. **Test token acquisition:**
   ```bash
   curl -X POST http://localhost:8042/dicomweb-oauth/servers/SERVER_NAME/test
   ```

2. **Check token format:**
   - Should be JWT (three base64 segments separated by dots)
   - Use jwt.io to decode and inspect claims

3. **Verify server configuration:**
   - Check DICOMweb server logs
   - Verify server configured to accept OAuth tokens
   - Ensure server has correct public key/JWKS URL

### Error: 403 Forbidden from DICOMweb server

**Causes:**
- Token valid but lacks required permissions
- Wrong scope requested

**Solutions:**

1. **Check token claims:**
   ```bash
   # Get token and decode
   curl -X POST http://localhost:8042/dicomweb-oauth/servers/SERVER_NAME/test
   # Copy token and check at jwt.io
   ```

2. **Verify required scopes/roles:**
   - Azure: Check RBAC role assignments
   - Keycloak: Check client roles and mappings
   - Review OAuth provider documentation

3. **Request broader scope:**
   ```json
   {
     "Scope": "https://resource/.default"  // Azure pattern for all permissions
   }
   ```

## Performance Issues

### Issue: Slow first request

**Expected:** First request acquires token (network call)

**Workaround:** Use test endpoint to pre-warm cache:
```bash
curl -X POST http://localhost:8042/dicomweb-oauth/servers/SERVER_NAME/test
```

### Issue: Frequent token refreshes

**Cause:** `TokenRefreshBufferSeconds` too large

**Solution:** Reduce buffer:
```json
{
  "TokenRefreshBufferSeconds": 120  // 2 minutes instead of 5
}
```

### Issue: Requests timing out

**Causes:**
- Token acquisition taking too long
- Network issues

**Debug:**
```bash
# Check token acquisition time
time curl -X POST http://localhost:8042/dicomweb-oauth/servers/SERVER_NAME/test
```

## Monitoring and Debugging

### Enable Verbose Logging

**orthanc.json:**
```json
{
  "Verbosity": "trace",
  "LogLevel": "default"
}
```

### Check Plugin Status

```bash
# Overall status
curl http://localhost:8042/dicomweb-oauth/status

# Server details
curl http://localhost:8042/dicomweb-oauth/servers

# Test specific server
curl -X POST http://localhost:8042/dicomweb-oauth/servers/SERVER_NAME/test
```

### View Logs

```bash
# All logs
docker-compose logs -f orthanc

# OAuth-specific
docker-compose logs orthanc | grep -i "oauth\|token"

# Errors only
docker-compose logs orthanc | grep -i error
```

### Common Log Messages

**Success:**
```
Token acquired for server 'X', expires in 3600 seconds
Using cached token for server 'X'
```

**Warnings:**
```
Token acquisition attempt 1 failed for server 'X': Connection timeout. Retrying in 1s...
```

**Errors:**
```
Failed to acquire token for server 'X': 401 Client Error
Environment variable 'CLIENT_SECRET' referenced in config but not set
```

## Getting Help

If issues persist:

1. **Collect information:**
   - Orthanc version
   - Plugin configuration (sanitized)
   - Full error logs
   - OAuth provider type

2. **Test token acquisition manually:**
   ```bash
   curl -X POST https://your-token-endpoint/token \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "grant_type=client_credentials" \
     -d "client_id=YOUR_ID" \
     -d "client_secret=YOUR_SECRET" \
     -d "scope=YOUR_SCOPE"
   ```

3. **Create GitHub issue** with:
   - Problem description
   - Steps to reproduce
   - Collected information
   - Sanitized logs

## References

- [OAuth 2.0 Troubleshooting](https://www.oauth.com/oauth2-servers/access-tokens/access-token-response/)
- [Orthanc Book](https://book.orthanc-server.com/)
- [Project GitHub Issues](https://github.com/yourusername/orthanc-dicomweb-oauth/issues)
