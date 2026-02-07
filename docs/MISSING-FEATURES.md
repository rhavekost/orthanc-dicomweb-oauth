# Missing Features & Future Work

This document explicitly lists features that are **not implemented** in this plugin, explains why, and describes when they might be needed.

## OAuth2 Flows

### ❌ Authorization Code Flow

**What it is:** User logs in via browser, gets redirected to application

**Why not included:**
- Orthanc is a server, not a web application
- No web UI for OAuth redirects
- DICOM workflows can't pause for user login
- See [OAUTH-FLOWS.md](OAUTH-FLOWS.md)

**When you'd need it:**
- Building a user-facing DICOM viewer
- Interactive web application (not Orthanc plugin)

**Alternative:**
- Use Orthanc's built-in authentication
- Build separate web app with OAuth2, connect to Orthanc

---

### ❌ Refresh Token Flow

**What it is:** Long-lived token that gets new access tokens without re-authenticating

**Why not included:**
- Client credentials flow doesn't use refresh tokens
- Providers (Azure, Google) don't issue refresh tokens for client credentials
- Access tokens are requested directly when expired

**When you'd need it:**
- Interactive user sessions (authorization code flow)
- Not applicable to service accounts

**Alternative:**
- Current implementation already handles token refresh (request new access token)

---

### ❌ Device Code Flow

**What it is:** User enters code on separate device to authenticate

**Why not included:**
- Requires user interaction
- Rare in DICOM/healthcare workflows
- Not supported by most healthcare APIs

**When you'd need it:**
- Medical devices without web browsers
- Very specialized embedded systems

**Alternative:**
- Use client credentials with service account
- Most medical devices don't need this

---

### ❌ Implicit Flow

**What it is:** Browser-based flow returning token directly (deprecated)

**Why not included:**
- **Deprecated** by OAuth2 spec (security risk)
- Not recommended by any provider
- No use case in server-to-server

**Alternative:**
- Use authorization code flow with PKCE (if you need browser-based auth)

---

### ❌ Password Grant Flow

**What it is:** User provides username/password directly to application (deprecated)

**Why not included:**
- **Deprecated** by OAuth2 spec (security risk)
- Not recommended by any provider
- Anti-pattern for modern authentication

**Alternative:**
- Use client credentials for service accounts
- Use authorization code flow for user authentication

---

## Distributed Caching

### ❌ Redis/Memcached Token Cache

**What it is:** Share tokens across multiple Orthanc instances

**Why not included:**
- Most deployments use single Orthanc instance
- Adds complexity and dependencies
- Token refresh is fast (< 1 second)

**When you'd need it:**
- Multiple Orthanc instances sharing OAuth config
- High-availability deployments
- Load-balanced Orthanc cluster

**Workaround:**
- Each Orthanc instance gets its own token (acceptable overhead)
- Tokens are cached locally (in-memory)

**Implementation effort:** 2-3 days (if needed)

---

## Horizontal Scaling

### ❌ Multi-Instance Token Coordination

**What it is:** Coordinate token refresh across Orthanc cluster

**Why not included:**
- Current design: in-memory cache per instance
- Requires distributed cache (Redis)
- Most deployments don't need this

**When you'd need it:**
- Orthanc cluster (5+ instances)
- Load-balanced production environment
- Shared token quota limits

**Workaround:**
- Each instance caches independently
- OAuth providers handle concurrent token requests fine

**Implementation effort:** 3-4 days (requires distributed cache)

---

## Advanced Error Handling

### ❌ Circuit Breaker Pattern

**What it is:** Stop calling failing services to prevent cascading failures

**Why not included:**
- Current retry logic with exponential backoff is sufficient
- Adds complexity
- OAuth providers are highly available

**When you'd need it:**
- Unreliable OAuth provider
- Need to fail fast after repeated errors
- Prevent resource exhaustion

**Current alternative:**
- Exponential backoff (3 retries, max 4 seconds)
- Timeout after 30 seconds
- See [RESILIENCE.md](RESILIENCE.md)

**Implementation effort:** 2 days (if needed in future)

---

### ❌ Fallback Authentication

**What it is:** Use backup auth method if OAuth fails

**Why not included:**
- No standard fallback mechanism
- Complicates security model
- OAuth should be reliable enough

**When you'd need it:**
- Critical systems requiring 100% uptime
- Backup to API keys or basic auth

**Security risk:** Having fallback auth reduces security

---

## Provider Optimizations

### ✅ Azure - Implemented
### ✅ Google - Implemented (new)
### ✅ AWS - Implemented (new)

### ❌ Specialized Providers: Okta, Auth0, Keycloak

**Why generic provider is sufficient:**
- These follow OAuth2 spec exactly
- No provider-specific optimizations needed
- Generic provider works perfectly

**When you'd need specialized classes:**
- Provider-specific error handling
- Special token validation logic
- Provider SDK integration

**Implementation effort:** 4-6 hours per provider (if needed)

---

## Token Validation

### ❌ JWT Signature Verification (for Generic Provider)

**What it is:** Verify JWT token signature using provider's public keys

**Why not included (for generic):**
- Only in specialized providers (Azure, Google, AWS)
- Generic provider trusts OAuth provider's response
- Most providers validate on their end

**When you'd need it:**
- Building security-critical application
- Want defense-in-depth
- Regulatory requirements

**Workaround:**
- Use specialized provider class (Azure, Google, AWS) which include validation
- Trust OAuth provider's validation

**Implementation effort:** 1 day per provider

---

## mTLS (Mutual TLS)

### ❌ Certificate-Based Authentication

**What it is:** Use client certificates instead of client secrets

**Why not included:**
- OAuth2 client credentials is standard
- Certificate management complexity
- Not all providers support mTLS
- Out of scope for this plugin

**When you'd need it:**
- Maximum security requirements
- Provider requires mTLS
- Zero-trust architecture

**Alternative:**
- Keep secrets secure (environment variables, secret managers)
- Use short-lived credentials
- Rotate secrets regularly

**Implementation effort:** 1-2 weeks (significant change)

---

## Monitoring & Observability

### ❌ Distributed Tracing (OpenTelemetry)

**What it is:** Trace requests across services

**Why not included:**
- Current structured logging is sufficient
- Adds dependencies (OpenTelemetry SDK)
- Most deployments don't need distributed tracing

**When you'd need it:**
- Microservices architecture
- Complex request flows
- Performance debugging at scale

**Current alternative:**
- Correlation IDs in logs
- Prometheus metrics
- See [METRICS.md](METRICS.md)

**Implementation effort:** 2-3 days

---

### ❌ Custom Metrics Backends (DataDog, New Relic)

**What it is:** Send metrics to commercial monitoring services

**Why not included:**
- Prometheus is standard
- Vendor-specific integration
- Can be added via Prometheus exporters

**When you'd need it:**
- Enterprise monitoring requirements
- Vendor-specific dashboards

**Alternative:**
- Use Prometheus (already supported)
- Export Prometheus to DataDog/New Relic

---

## Configuration

### ❌ Dynamic Configuration Reloading

**What it is:** Change configuration without restarting Orthanc

**Why not included:**
- Orthanc doesn't support plugin config reload
- Requires Orthanc restart anyway
- Adds complexity

**When you'd need it:**
- Frequent config changes
- Zero-downtime config updates

**Workaround:**
- Use environment variables for secrets (can be changed)
- Use rolling restarts in Kubernetes

**Implementation effort:** 3-4 days (limited by Orthanc architecture)

---

### ❌ Web UI for Configuration

**What it is:** Configure plugin via web interface

**Why not included:**
- Orthanc config is JSON-based
- Security risk (exposing secrets)
- Infrastructure-as-code is better practice

**When you'd need it:**
- Non-technical users managing Orthanc
- Visual configuration preference

**Alternative:**
- Edit `orthanc.json` directly (standard practice)
- Use configuration management tools (Ansible, Terraform)

---

## API Features

### ❌ Token Introspection Endpoint

**What it is:** API to check token validity

**Why not included:**
- Tokens are cached internally
- No external need to check token validity
- Would expose token details

**When you'd need it:**
- External services need to check Orthanc's token
- Debugging token issues

**Workaround:**
- Use `/dicomweb-oauth/servers/{name}/test` endpoint

---

### ❌ Token Revocation API

**What it is:** API to manually invalidate cached token

**Why not included:**
- Tokens expire automatically
- Restart Orthanc to clear cache
- Limited use case

**When you'd need it:**
- Suspected token compromise
- Testing token refresh logic

**Workaround:**
- Restart Orthanc container/service
- Wait for token to expire (typically 1 hour)

**Implementation effort:** 2-3 hours (if needed)

---

## Testing

### ❌ Integration Test Suite with Real Providers

**What it is:** Automated tests against actual Azure, Google, AWS

**Why not included:**
- Requires credentials for CI
- Costs money (API calls)
- Security risk (credentials in CI)

**Current alternative:**
- Mock-based unit tests (comprehensive)
- Manual testing against real providers
- Docker-based integration tests

**When you'd need it:**
- Regular provider API changes
- Regression detection across providers

---

## Documentation

### ❌ OpenAPI/Swagger Specification

**What it is:** Machine-readable API documentation

**Why not included:**
- Simple REST API (3 endpoints)
- Documented in README and code
- Limited external API usage

**When you'd need it:**
- Building tools that consume the API
- Automatic client generation

**Implementation effort:** 4-6 hours

---

## Summary: What's NOT Included

| Feature | Reason | Workaround | Effort If Needed |
|---------|--------|------------|------------------|
| Authorization code flow | No web UI in Orthanc | Separate web app | N/A |
| Refresh token flow | Not used with client credentials | Current impl. is sufficient | N/A |
| Distributed caching | Single-instance focus | Per-instance cache | 2-3 days |
| Circuit breaker | Current retry is sufficient | Exponential backoff | 2 days |
| mTLS | Out of scope | Secure secret management | 1-2 weeks |
| JWT validation (generic) | Use specialized providers | Trust OAuth provider | 1 day |
| Dynamic config reload | Orthanc limitation | Restart Orthanc | 3-4 days |
| Web UI config | Security/complexity | Edit JSON config | N/A |
| Distributed tracing | Logging is sufficient | Correlation IDs | 2-3 days |

## Feature Requests Welcome

If you need any of these features:

1. Open an issue explaining your use case
2. Describe why the current workaround doesn't work
3. Consider contributing! See [CONTRIBUTING.md](CONTRIBUTING.md)

We prioritize features based on:
- ✅ Real use cases (not theoretical)
- ✅ Number of users requesting it
- ✅ Alignment with plugin's mission (OAuth2 for DICOMweb)
- ✅ Implementation complexity vs. benefit
