# ADR 002: No Feature Flags for Orthanc Plugin

**Status:** Accepted
**Date:** 2026-02-07
**Decision Makers:** Development Team

## Context

During the project assessment, we evaluated whether feature flags would benefit the Orthanc DICOMweb OAuth plugin for gradual rollout and A/B testing of new features.

## Decision

We have decided **NOT to implement feature flags** for the following reasons:

## Rationale

### 1. Single-Tenant Deployment Model
- Each Orthanc instance serves a single organization/facility
- No multi-tenant SaaS model requiring per-tenant feature toggles
- Feature rollouts happen via version upgrades, not runtime flags

### 2. Plugin Architecture Constraints
- Orthanc loads plugins once at startup
- Runtime feature toggling would require plugin restart anyway
- No benefit over configuration-based approaches

### 3. Simple Configuration is Sufficient
- OAuth provider selection via `ProviderType` config field
- Server-specific settings via JSON configuration
- Environment-based configuration (dev, staging, prod) meets needs

### 4. Deployment Pattern
- Healthcare environments follow careful, planned deployments
- No continuous deployment with percentage-based rollouts
- Canary deployments done at infrastructure level (multiple instances)

### 5. Complexity vs. Benefit
- Feature flags add significant complexity:
  - Flag storage and management
  - Runtime flag evaluation
  - Flag cleanup and technical debt
- Minimal benefit for single-tenant plugin architecture

## Alternatives Considered

1. **LaunchDarkly/Unleash Integration**
   - Rejected: Too complex for plugin use case
   - Better suited for web applications with many users

2. **Config-based Feature Toggles**
   - Partially adopted: Use configuration for provider selection
   - Sufficient for our needs without flag infrastructure

3. **Environment Variables**
   - Already used for environment separation
   - Simple and effective for binary on/off features

## Consequences

### Positive
- ✅ Simpler codebase without flag management code
- ✅ Less runtime overhead (no flag evaluation)
- ✅ Easier testing (fewer combinations to test)
- ✅ Configuration-based approach is well understood

### Negative
- ❌ Cannot toggle features without config change + restart
- ❌ No gradual percentage-based rollouts (not needed anyway)

### Neutral
- Configuration remains the single source of truth for behavior
- New features enabled via version upgrades and config updates

## Implementation

Use configuration-based feature selection:

```json
{
  "DicomWebOAuth": {
    "Servers": {
      "my-server": {
        "ProviderType": "azure",  // Feature selection via config
        "EnableTokenValidation": true,  // Feature toggle via config
        "EnableMetrics": false
      }
    }
  }
}
```

## Review Date

This decision should be reviewed if:
- Plugin moves to multi-tenant SaaS model
- Continuous deployment becomes standard in healthcare
- Regulatory requirements change around feature control

## References

- [Feature Toggles (Martin Fowler)](https://martinfowler.com/articles/feature-toggles.html)
- PROJECT-ASSESSMENT-REPORT.md - Environment Separation section
