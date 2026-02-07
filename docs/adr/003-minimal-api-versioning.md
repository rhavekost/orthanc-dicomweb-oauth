# ADR 003: Minimal API Versioning Strategy

**Status:** Accepted
**Date:** 2026-02-07
**Decision Makers:** Development Team

## Context

The project assessment flagged lack of API versioning as a concern. The plugin exposes REST endpoints for status, server listing, and testing. We need to decide on an API versioning strategy.

## Decision

Implement **minimal versioning** with the following approach:

1. **No URL versioning initially** (keep `/dicomweb-oauth/*`)
2. **Version headers** for future compatibility
3. **Backward compatibility guarantees** via semantic versioning
4. **Deprecation warnings** before breaking changes

## Rationale

### Current State Analysis

The plugin exposes a small, stable API surface:
- `GET /dicomweb-oauth/status` - Plugin health check
- `GET /dicomweb-oauth/servers` - List configured servers
- `POST /dicomweb-oauth/servers/{name}/test` - Test token acquisition

### Why NOT URL Versioning (`/v1/`, `/v2/`)

1. **Small API Surface**: Only 3 endpoints with simple contracts
2. **Internal API**: Consumed by administrators, not external developers
3. **Orthanc Constraints**: No built-in API gateway for path-based routing
4. **Maintenance Burden**: Multiple versions = multiple codepaths to maintain

### Why Minimal Versioning IS Sufficient

1. **Semantic Versioning Already in Place**
   - Plugin version in response headers
   - Changelog tracks breaking changes
   - Users can pin to specific versions

2. **Response Evolution Without Breaking Changes**
   - Add new fields (backward compatible)
   - Optional fields with defaults (backward compatible)
   - Deprecation warnings before removal

3. **Administrative Use Case**
   - Not a public API with many consumers
   - Changes coordinated with infrastructure updates
   - Breaking changes acceptable with proper notice

## Implementation Strategy

### Phase 1: Version Headers (Immediate)

Add version information to all responses:

```json
{
  "plugin_version": "2.0.0",
  "api_version": "2.0",
  "data": { ... }
}
```

### Phase 2: Deprecation Warnings (Before Breaking Changes)

When deprecating a field:

```json
{
  "plugin_version": "2.1.0",
  "api_version": "2.1",
  "data": {
    "old_field": "value",
    "_deprecated": {
      "old_field": "Deprecated in 2.1.0, will be removed in 3.0.0. Use new_field instead."
    },
    "new_field": "value"
  }
}
```

### Phase 3: URL Versioning (If Needed)

Only if we have:
- Multiple major versions to support simultaneously
- External API consumers requiring stability guarantees
- Complex breaking changes requiring parallel APIs

Then add: `/dicomweb-oauth/v2/status`

## Semantic Versioning Contract

Plugin follows semantic versioning:

- **Major version (X.0.0)**: Breaking API changes
  - Remove deprecated fields
  - Change response structure
  - Require migration

- **Minor version (0.X.0)**: Backward-compatible additions
  - Add new endpoints
  - Add new fields to responses
  - Add optional parameters

- **Patch version (0.0.X)**: Bug fixes only
  - No API changes
  - Internal fixes

## Breaking Change Process

Before making a breaking change:

1. **Announce deprecation** (1-2 minor versions in advance)
2. **Add warnings to responses** (JSON `_deprecated` field)
3. **Update documentation** (mark as deprecated)
4. **Wait for major version** (remove only in X.0.0)

## Alternatives Considered

### Alternative 1: URL Versioning from Start
```
/dicomweb-oauth/v1/status
/dicomweb-oauth/v1/servers
```

**Rejected:**
- Over-engineering for 3 simple endpoints
- Adds complexity without clear benefit
- Orthanc doesn't provide API gateway features

### Alternative 2: No Versioning at All

**Rejected:**
- No way to introduce breaking changes gracefully
- No version discovery mechanism
- Fails best practices for APIs

### Alternative 3: GraphQL

**Rejected:**
- Massive overkill for simple status API
- Not aligned with Orthanc's REST-based approach

## Implementation

### Current Endpoints (No URL Version)

```
GET  /dicomweb-oauth/status
GET  /dicomweb-oauth/servers
POST /dicomweb-oauth/servers/{name}/test
```

### Response Format (With Version Headers)

```json
{
  "plugin_version": "2.0.0",
  "api_version": "2.0",
  "status": "healthy",
  "timestamp": "2026-02-07T10:30:00Z",
  "data": {
    "token_managers": 1,
    "servers_configured": 1
  }
}
```

### Future (If URL Versioning Needed)

```
/dicomweb-oauth/v2/status    # New version
/dicomweb-oauth/status       # Redirects to /v2/ with warning
```

## Consequences

### Positive
- ✅ Simple to implement and maintain
- ✅ Clear versioning through plugin version
- ✅ Graceful deprecation path
- ✅ Minimal overhead

### Negative
- ❌ Cannot run multiple API versions simultaneously
- ❌ Breaking changes affect all consumers at once

### Mitigation
- Use semantic versioning strictly
- Deprecate fields 2+ minor versions before removal
- Communicate breaking changes in CHANGELOG
- Provide migration guides for major versions

## Review Date

Review this decision if:
- Plugin becomes public API with many consumers
- Need to support multiple major versions simultaneously
- Orthanc adds API gateway features
- External monitoring systems require stable contracts

## References

- [Semantic Versioning 2.0.0](https://semver.org/)
- [API Versioning Best Practices](https://restfulapi.net/versioning/)
- PROJECT-ASSESSMENT-REPORT.md - API Versioning section
