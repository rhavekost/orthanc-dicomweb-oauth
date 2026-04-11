# Orthanc DICOMweb OAuth Plugin

Enables [Orthanc](https://www.orthanc-server.com/) to transparently connect to OAuth2-protected DICOMweb servers. Automatically handles token acquisition, caching, and refresh — users simply click "Send to DICOMWeb server" as usual.

**GitHub:** [rhavekost/orthanc-dicomweb-oauth](https://github.com/rhavekost/orthanc-dicomweb-oauth)

---

## Available Tags

| Tag | Description |
|-----|-------------|
| `latest-plugin` | Plugin files only — use as init container alongside any Orthanc image |
| `X.Y.Z-plugin` | Pinned version of plugin-only image (recommended for production) |
| `latest` | Standalone image: Orthanc + Python plugin + all dependencies |
| `X.Y.Z` | Pinned version of standalone image |

**Recommended for production:** pin to a specific version, e.g. `2.2.2-plugin`

---

## Quick Start

### Option 1: Init Container (Recommended)

Use the plugin-only image alongside any standard Orthanc image. This keeps the plugin decoupled from your base image and lets you upgrade each independently.

**Docker Compose:**

```yaml
services:
  orthanc:
    image: orthancteam/orthanc:latest-full
    environment:
      PYTHONPATH: /etc/orthanc/plugins
    volumes:
      - plugin-volume:/etc/orthanc/plugins/plugin
    depends_on:
      plugin-install:
        condition: service_completed_successfully

  plugin-install:
    image: rhavekost/orthanc-dicomweb-oauth:2.2.2-plugin
    command: ["sh", "-c", "cp -r /plugin/. /target/"]
    volumes:
      - plugin-volume:/target

volumes:
  plugin-volume:
```

**Kubernetes:**

```yaml
initContainers:
  - name: plugin-install
    image: rhavekost/orthanc-dicomweb-oauth:2.2.2-plugin
    command: ["sh", "-c", "cp -r /plugin/. /target/"]
    volumeMounts:
      - name: plugin-volume
        mountPath: /target

containers:
  - name: orthanc
    image: orthancteam/orthanc:latest-full
    env:
      - name: PYTHONPATH
        value: /etc/orthanc/plugins
    volumeMounts:
      - name: plugin-volume
        mountPath: /etc/orthanc/plugins/plugin
```

### Option 2: Standalone Image

```bash
docker run -d \
  -p 8042:8042 \
  -v /path/to/orthanc.json:/etc/orthanc/orthanc.json \
  rhavekost/orthanc-dicomweb-oauth:2.2.2
```

---

## How It Works

1. Configure your DICOMweb server URL to point to the local OAuth proxy endpoint
2. User selects a study and clicks "Send to DICOMWeb server" in Orthanc Explorer
3. The plugin transparently:
   - Acquires an OAuth token from your provider (Azure AD, Google, AWS, etc.)
   - Caches the token and refreshes it proactively before expiration
   - Forwards the DICOM data to the target server with a `Bearer` token

No manual token management. No workflow changes for end users.

---

## Configuration

Add a `DicomWebOAuth` section to your `orthanc.json`:

```json
{
  "DicomWeb": {
    "Servers": {
      "my-server": {
        "Url": "http://localhost:8042/oauth-dicom-web/servers/my-server",
        "Username": "admin",
        "Password": "orthanc"
      }
    }
  },
  "DicomWebOAuth": {
    "Servers": {
      "my-server": {
        "Url": "https://your-dicom-endpoint.example.com/v1",
        "TokenEndpoint": "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token",
        "ClientId": "${CLIENT_ID}",
        "ClientSecret": "${CLIENT_SECRET}",
        "Scope": "https://dicom.healthcareapis.azure.com/.default"
      }
    }
  }
}
```

Use `${ENV_VAR}` syntax to inject secrets from environment variables — never hardcode credentials in config files.

---

## Features

- **Generic OAuth2** — works with any OAuth2/OIDC provider; verified with Azure Entra ID
- **Provider auto-detection** — detects Azure, Google, AWS from the token endpoint URL
- **Azure Managed Identity** — zero-secrets authentication for Azure deployments
- **Distributed caching** — Redis support for multi-replica horizontal scaling
- **Circuit breaker** — prevents cascading failures
- **Prometheus metrics** — `/dicomweb-oauth/metrics` endpoint
- **HIPAA compliance docs** — included in the GitHub repository
- **JWT validation** — verifies token integrity and claims
- **Rate limiting** — configurable per-endpoint limits

---

## Verified Providers

| Provider | Status |
|----------|--------|
| Azure Health Data Services DICOM | Verified |
| Azure Entra ID (client credentials) | Verified |
| Azure Managed Identity | Verified |
| Google Cloud Healthcare API | Code implemented, not yet tested |
| AWS HealthImaging | Code implemented, not yet tested |
| Other OAuth2/OIDC providers | Should work, not yet tested |

---

## Azure Quickstart

A complete working example for Azure is included in the GitHub repository under `examples/azure/quickstart/`. It provisions all required Azure resources and deploys Orthanc with the plugin in about 15 minutes.

See the [Azure Quickstart Guide](https://github.com/rhavekost/orthanc-dicomweb-oauth/tree/main/examples/azure/quickstart) for step-by-step instructions.

---

## Security Notice

This plugin handles medical imaging data and OAuth credentials. Before production deployment:

- Store all credentials in environment variables or a secrets manager — never in config files
- Enable TLS for all endpoints
- Review the [Security Best Practices](https://github.com/rhavekost/orthanc-dicomweb-oauth/blob/main/docs/security/BEST-PRACTICES.md) documentation
- Review HIPAA compliance documentation if operating in a healthcare context

---

## License

MIT — [Rob Havekost](https://github.com/rhavekost)
