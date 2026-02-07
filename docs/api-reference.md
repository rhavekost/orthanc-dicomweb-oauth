# API Reference

## Overview

The Orthanc DICOMweb OAuth plugin exposes a REST API for monitoring and testing OAuth token management.

**Base URL:** `http://localhost:8042/dicomweb-oauth`

**API Version:** 2.0

## Versioning

All responses include version information:

```json
{
  "plugin_version": "2.0.0",  // Full plugin version
  "api_version": "2.0",        // API compatibility version (Major.Minor)
  "timestamp": "2026-02-07T10:30:00Z",
  "data": { ... }
}
```

### Semantic Versioning Contract

- **Major version change (X.0)**: Breaking changes, may require client updates
- **Minor version change (0.X)**: Backward-compatible additions
- **Patch version (plugin_version)**: Bug fixes only, no API changes

### Deprecation Policy

Deprecated fields will:
1. Include `_deprecated` notice in response
2. Remain functional for 2+ minor versions
3. Be removed only in next major version

Example of deprecated field:

```json
{
  "data": {
    "old_field": "value",
    "_deprecated": {
      "old_field": "Deprecated in 2.1.0, will be removed in 3.0.0. Use new_field instead."
    },
    "new_field": "value"
  }
}
```

## Endpoints

### GET /dicomweb-oauth/status

Check plugin health and basic metrics.

**Response 200 OK:**
```json
{
  "plugin_version": "2.0.0",
  "api_version": "2.0",
  "timestamp": "2026-02-07T10:30:00Z",
  "data": {
    "status": "healthy",
    "token_managers": 1,
    "servers_configured": 1
  }
}
```

### GET /dicomweb-oauth/servers

List all configured OAuth servers.

**Response 200 OK:**
```json
{
  "plugin_version": "2.0.0",
  "api_version": "2.0",
  "timestamp": "2026-02-07T10:30:00Z",
  "data": {
    "servers": ["azure-dicom", "keycloak-dicom"]
  }
}
```

### POST /dicomweb-oauth/servers/{name}/test

Test token acquisition for a specific server.

**Parameters:**
- `name` (path): Server name from configuration

**Response 200 OK:**
```json
{
  "plugin_version": "2.0.0",
  "api_version": "2.0",
  "timestamp": "2026-02-07T10:30:00Z",
  "data": {
    "server": "azure-dicom",
    "status": "success",
    "token_preview": "eyJhbGc...",
    "expires_in": 3600
  }
}
```

**Response 400 Bad Request:**
```json
{
  "plugin_version": "2.0.0",
  "api_version": "2.0",
  "timestamp": "2026-02-07T10:30:00Z",
  "data": {
    "error": "Server 'unknown' not found"
  }
}
```

## Error Handling

All errors include version information and follow the same structure:

```json
{
  "plugin_version": "2.0.0",
  "api_version": "2.0",
  "timestamp": "2026-02-07T10:30:00Z",
  "data": {
    "error": "Error message",
    "error_type": "TokenAcquisitionError"
  }
}
```

## Examples

### Using curl

```bash
# Check status
curl http://localhost:8042/dicomweb-oauth/status

# List servers
curl http://localhost:8042/dicomweb-oauth/servers

# Test server
curl -X POST http://localhost:8042/dicomweb-oauth/servers/azure-dicom/test
```

### Using Python

```python
import requests

base_url = "http://localhost:8042/dicomweb-oauth"

# Check status
response = requests.get(f"{base_url}/status")
print(f"Plugin version: {response.json()['plugin_version']}")
print(f"API version: {response.json()['api_version']}")

# List servers
response = requests.get(f"{base_url}/servers")
servers = response.json()['data']['servers']
print(f"Configured servers: {servers}")

# Test server
response = requests.post(f"{base_url}/servers/azure-dicom/test")
if response.ok:
    print("Token acquisition successful")
```

## Version History

- **API Version 2.0** (Plugin 2.0.0)
  - Added version information to all responses
  - Added timestamp field
  - Standardized response structure

- **API Version 1.0** (Plugin 1.x)
  - Initial REST API
  - Basic status and server endpoints
