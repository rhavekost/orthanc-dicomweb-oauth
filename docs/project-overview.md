# orthanc-dicomweb-oauth

**GitHub repo name:** `orthanc-dicomweb-oauth`

Generic OAuth2/OIDC token management plugin for Orthanc's DICOMweb connections. Automatically acquires, caches, and refreshes bearer tokens for any OAuth2-protected DICOMweb endpoint.

## Problem Statement

Orthanc's DICOMweb plugin only supports HTTP Basic auth or static headers. Any DICOMweb server behind OAuth2 authentication is unreachable because tokens expire (typically hourly) and Orthanc has no way to refresh them.

This affects every major cloud DICOM service and any on-prem DICOMweb server behind an identity provider:

- **Azure Health Data Services** — OAuth2 via Microsoft Entra ID — ❌ no Orthanc plugin
- **Google Cloud Healthcare API** — ✅ has official C++ plugin (see Existing Solutions)
- **AWS HealthImaging** — SigV4 / OAuth2 — ❌ no Orthanc plugin
- **Any DICOMweb server behind Keycloak, Auth0, Okta, etc.** — ❌ no Orthanc plugin

The underlying protocol is identical: OAuth2 client credentials flow → bearer token → `Authorization` header. Only the token endpoint URL and scopes differ.

### Existing Solutions & Competitive Landscape

**Orthanc Google Cloud Platform Plugin (Official)**
- C++ plugin maintained by Orthanc team
- Handles OAuth token acquisition and periodic refresh for Google Cloud Healthcare API
- Supports service account auth and user account auth
- Registers DICOMweb servers automatically
- Built on Google Cloud C++ Client Libraries — must be compiled from source, no pre-built binaries
- **Google-only.** Does not work with Azure, Keycloak, or any other provider.
- [Docs](https://orthanc.uclouvain.be/book/plugins/google-cloud-platform.html)

**Orthanc Authorization Plugin (Official)**
- Handles *inbound* auth — validates tokens on requests TO Orthanc
- Works with Keycloak via orthanc-auth-service companion project
- Does NOT handle *outbound* connections FROM Orthanc to external DICOMweb servers
- Completely different problem from what we're solving

**colbyford/orthanc-on-azure**
- Hardcoded JWT in config file — not a real solution
- Token expires, Orthanc breaks, manual intervention required

**Key insight:** The Orthanc team built a provider-specific C++ plugin for Google. Nobody has built the equivalent for Azure or for generic OAuth2. Our plugin fills that gap for everyone — and as a Python plugin with zero compilation required, it's dramatically easier to deploy than the GCP C++ plugin.

### Current Workarounds (All Painful)

- **Proxy middleware** to intercept requests and inject fresh tokens (what Rob built at ResonAit with Node.js)
- Manually rotating tokens in config and restarting Orthanc
- Hardcoded bearer tokens in config files (see `colbyford/orthanc-on-azure`)
- External reverse proxy (nginx/caddy) that handles token injection

### Confirmed Community Demand

- Orthanc forum post (May 2025): "Using DICOMweb STOW-RS with Azure Health Data Services" — user stuck on tenant ID + OAuth
- Orthanc forum (May 2024): "Authorization Plugin doesn't like bearer prefix" — user trying to use Keycloak tokens with DICOMweb
- No generic OAuth2 solution exists in the Orthanc plugin ecosystem
- The GCP plugin's existence proves the Orthanc team recognizes this is a real need — they just only solved it for Google

---

## Tiered Implementation

### Tier 1: Generic OAuth2 Plugin (Ship First)

Standard OAuth2 client credentials flow. Works with any OIDC-compliant provider. No provider-specific libraries required.

**Dependencies:** `requests` only.

**Configuration:**

```json
{
  "DicomWebOAuth": {
    "Servers": {
      "my-cloud-dicom": {
        "Url": "https://dicom.example.com/v2/",
        "TokenEndpoint": "https://login.example.com/oauth2/token",
        "ClientId": "xxxxxxxx",
        "ClientSecret": "your-client-secret",
        "Scope": "https://dicom.example.com/.default",
        "TokenRefreshBufferSeconds": 300
      }
    }
  }
}
```

**Provider examples with Tier 1:**

Azure Entra ID:
```json
{
  "TokenEndpoint": "https://login.microsoftonline.com/{tenant-id}/oauth2/v2.0/token",
  "Scope": "https://dicom.healthcareapis.azure.com/.default"
}
```

Google Cloud (lighter alternative to C++ plugin):
```json
{
  "TokenEndpoint": "https://oauth2.googleapis.com/token",
  "Scope": "https://www.googleapis.com/auth/cloud-healthcare"
}
```

Keycloak:
```json
{
  "TokenEndpoint": "https://keycloak.example.com/realms/myrealm/protocol/openid-connect/token",
  "Scope": "dicomweb"
}
```

### Tier 2: Azure-Specific Extension (Add After Tier 1)

Adds MSAL + `azure-identity` for managed identity support. When Orthanc runs in Azure Container Apps, AKS, or Azure VMs, it authenticates with zero credentials in config — the Azure platform handles it.

**Additional dependencies:** `msal`, `azure-identity`

**Managed identity config:**
```json
{
  "DicomWebOAuth": {
    "Servers": {
      "azure-dicom": {
        "Url": "https://workspace-dicom.dicom.azurehealthcareapis.com/v2/",
        "Provider": "azure",
        "Scope": "https://dicom.healthcareapis.azure.com/.default",
        "UseManagedIdentity": true
      }
    }
  }
}
```

**How it works:** If `Provider: "azure"` is set and MSAL/azure-identity are installed, the plugin uses `ManagedIdentityCredential` or `ConfidentialClientApplication`. If those packages aren't installed, falls back to generic OAuth2 flow (Tier 1).

---

## Technical Design

### Implementation: Python Plugin

- Orthanc Python plugin SDK is well-documented
- `orthancteam/orthanc` Docker images include Python runtime
- Tier 1 needs only `requests` (already in most Python installs)
- Tier 2 adds optional `msal` + `azure-identity`
- **Advantage over GCP C++ plugin:** No compilation, pip install, works everywhere

### Architecture

```
┌──────────────────────────────────────────────────┐
│                    Orthanc                        │
│                                                   │
│  ┌─────────────┐    ┌───────────────────────────┐│
│  │  DICOMweb   │    │  dicomweb-oauth plugin    ││
│  │  Plugin     │◄───│                           ││
│  │             │    │  Tier 1: Generic OAuth2    ││
│  │  QIDO-RS    │    │  - Token endpoint call    ││
│  │  WADO-RS    │    │  - Token caching          ││
│  │  STOW-RS    │    │  - Auto-refresh           ││
│  │             │    │  - Header injection        ││
│  │             │    │                           ││
│  │             │    │  Tier 2: Azure (optional)  ││
│  │             │    │  - MSAL client credentials ││
│  │             │    │  - Managed identity        ││
│  └──────┬──────┘    └──────────┬────────────────┘│
└─────────┼──────────────────────┼─────────────────┘
          │                      │
          ▼                      ▼
   Any DICOMweb            Any OAuth2/OIDC
   Server                  Token Endpoint
```

### Token Lifecycle

1. **On startup:** Acquire initial token from configured token endpoint
2. **On each DICOMweb request:** Check cached token validity (with buffer)
3. **If expiring soon:** Proactively refresh before expiration
4. **If acquisition fails:** Log error, return 503 (don't send unauthenticated request)
5. **Token storage:** In-memory only — never persisted to disk

### Error Handling

- Token acquisition failure → log + HTTP 503 response
- Network timeout to token endpoint → retry with exponential backoff (max 3 attempts)
- Invalid credentials → clear error message referencing config fields
- Token refresh race condition → thread-safe caching

---

## API Surface

REST endpoints on Orthanc for monitoring/debugging:

```
GET /dicomweb-oauth/status
GET /dicomweb-oauth/servers
POST /dicomweb-oauth/servers/{name}/test
```

---

## Deployment

### Docker

```dockerfile
FROM orthancteam/orthanc:latest

# Tier 1: Generic OAuth2 (no extra deps needed beyond requests)
# Tier 2: Azure managed identity (optional)
RUN pip install msal azure-identity  # omit for Tier 1 only

COPY dicomweb-oauth-plugin.py /etc/orthanc/plugins/
COPY orthanc.json /etc/orthanc/
```

### Environment Variable Override

All config values support env var substitution for Docker/K8s secrets:
```json
{
  "DicomWebOAuth": {
    "Servers": {
      "cloud-dicom": {
        "ClientId": "${OAUTH_CLIENT_ID}",
        "ClientSecret": "${OAUTH_CLIENT_SECRET}"
      }
    }
  }
}
```

---

## Execution Plan

### Phase 1: Generic OAuth2 (1-2 evenings)
- [ ] Orthanc Python plugin dev environment
- [ ] OAuth2 client credentials token acquisition using `requests`
- [ ] Token caching with expiry-aware refresh
- [ ] HTTP header injection on outgoing DICOMweb requests
- [ ] Config parsing from `orthanc.json`
- [ ] Test against Azure (as first provider) and/or Keycloak
- [ ] Basic error logging

### Phase 2: Azure Extension (1 evening)
- [ ] Optional MSAL `ConfidentialClientApplication` integration
- [ ] Managed identity via `azure-identity` `ManagedIdentityCredential`
- [ ] `Provider: "azure"` config flag with graceful fallback if MSAL not installed
- [ ] Test in Azure Container Apps with system-assigned managed identity

### Phase 3: Production Hardening (1 weekend)
- [ ] Monitoring endpoints, retry logic, thread-safe refresh, env var config

### Phase 4: Documentation & Release
- [ ] README with quick-start per provider (Azure, Google, Keycloak)
- [ ] Docker Compose examples
- [ ] Azure Container Apps deployment guide (with managed identity)
- [ ] Orthanc forum announcement
- [ ] GitHub repo with MIT license
- [ ] LinkedIn post

### Phase 5: Community & Iteration
- [ ] Google Cloud testing (as lighter alternative to C++ plugin)
- [ ] AWS HealthImaging investigation
- [ ] Azure Government / sovereign clouds
- [ ] Optional: C++ port, upstream PR

---

## Success Criteria

- [ ] Orthanc can STOW-RS/QIDO-RS to any OAuth2-protected DICOMweb server
- [ ] Tokens refresh automatically without intervention
- [ ] Works with Azure, Google Cloud, and Keycloak out of the box
- [ ] Azure managed identity works with zero credentials in config
- [ ] At least one community member deploys successfully

---

## References

- [Orthanc DICOMweb Plugin Docs](https://orthanc.uclouvain.be/book/plugins/dicomweb.html)
- [Orthanc Python Plugin SDK](https://orthanc.uclouvain.be/book/plugins/python.html)
- [Orthanc GCP Plugin Docs](https://orthanc.uclouvain.be/book/plugins/google-cloud-platform.html) — existing Google-only solution
- [OAuth2 Client Credentials Flow (RFC 6749)](https://datatracker.ietf.org/doc/html/rfc6749#section-4.4)
- [Azure DICOM Service Auth](https://learn.microsoft.com/en-us/azure/healthcare-apis/dicom/get-access-token)
- [Google Cloud Healthcare API Auth](https://cloud.google.com/healthcare-api/docs/how-tos/controlling-access)
- [MSAL Python Library](https://github.com/AzureAD/microsoft-authentication-library-for-python)
- [colbyford/orthanc-on-azure](https://github.com/colbyford/orthanc-on-azure)
- [Orthanc Forum: DICOMweb STOW-RS with Azure](https://discourse.orthanc-server.org/t/using-dicomweb-stow-rs-with-azure-health-data-services/5902)
- [Orthanc Forum: Authorization Plugin + bearer prefix](https://discourse.orthanc-server.org/t/authorization-plugin-doesnt-like-bearer-prefix/4750)