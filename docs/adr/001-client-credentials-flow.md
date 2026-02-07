# ADR 001: OAuth2 Client Credentials Flow Only

**Status:** Accepted
**Date:** 2025-01 (retroactive documentation)
**Decision Makers:** Initial Project Team

## Context

The plugin needs to authenticate with OAuth2-protected DICOMweb servers. OAuth2 defines multiple grant types (flows) for different use cases:

1. **Authorization Code Flow** - User interactive, redirects to login page
2. **Client Credentials Flow** - Machine-to-machine, no user interaction
3. **Resource Owner Password Flow** - User provides credentials directly (deprecated)
4. **Implicit Flow** - Browser-based, deprecated for security reasons
5. **Device Code Flow** - For devices without browsers

Orthanc is a server application that needs automated access to DICOMweb endpoints without human interaction.

## Decision

Implement **Client Credentials Flow** only, with no support for other OAuth2 grant types.

## Rationale

### Why Client Credentials Flow?

1. **Server-to-Server Communication**
   - Orthanc is a backend service, not a user-facing application
   - No web UI for user authentication
   - Needs to connect automatically on startup

2. **DICOM Workflow Requirements**
   - DICOM routing happens automatically (C-STORE, C-FIND)
   - Cannot interrupt workflow to ask for user login
   - Service accounts are standard in healthcare IT

3. **Deployment Model**
   - Orthanc typically runs as a system service
   - No user present to authenticate
   - Credentials configured by administrators

4. **Industry Standard**
   - Azure Health Data Services uses client credentials
   - Google Cloud Healthcare API uses service accounts (similar concept)
   - Standard for M2M authentication

### Why NOT Authorization Code Flow?

- **Requires user interaction**: Cannot automate DICOM routing
- **Browser needed**: Orthanc has no web UI for OAuth redirects
- **Complexity**: Need to handle redirect URIs, state parameters
- **Not applicable**: No end-user credentials to protect

### Why NOT Refresh Tokens?

- **Client credentials don't use refresh tokens**: Token endpoint issues new access tokens directly
- **Simpler implementation**: Single token acquisition flow
- **Provider behavior**: Most providers (Azure, Google) don't issue refresh tokens for client credentials

## Alternatives Considered

### Alternative 1: Support Multiple Grant Types

**Pros:**
- Flexibility for different deployment scenarios
- Could support interactive use cases

**Cons:**
- Significantly more complex implementation
- No clear use case for interactive flows in DICOM context
- Increases attack surface
- More testing complexity

**Decision:** Rejected - YAGNI principle

### Alternative 2: Mutual TLS (mTLS)

**Pros:**
- More secure than shared secrets
- No secrets in configuration

**Cons:**
- Not OAuth2 - different protocol
- Certificate management complexity
- Not all providers support mTLS
- Requires PKI infrastructure

**Decision:** Out of scope - Could be future enhancement

### Alternative 3: API Keys

**Pros:**
- Simpler than OAuth2
- Static credentials

**Cons:**
- No expiration - security risk
- No scope-based permissions
- Not standardized
- Many providers moving away from API keys

**Decision:** Rejected - OAuth2 is industry standard

## Consequences

### Positive
- ✅ Simple, focused implementation
- ✅ Matches actual use cases
- ✅ Works with all major healthcare cloud providers
- ✅ Automated, no user interaction needed
- ✅ Easier to test and maintain

### Negative
- ❌ Cannot support interactive OAuth scenarios
- ❌ Not suitable for user-delegated access
- ❌ No support for personal Microsoft/Google accounts

### Neutral
- Plugin is designed for service-to-service authentication
- Interactive scenarios would need separate solution
- Aligns with Orthanc's server-side nature

## Implementation Notes

### Token Acquisition

```python
def _acquire_token(self) -> str:
    """Acquire access token using client credentials flow."""
    data = {
        "grant_type": "client_credentials",
        "client_id": self.client_id,
        "client_secret": self.client_secret,
        "scope": self.scope
    }

    response = requests.post(self.token_endpoint, data=data)
    return response.json()["access_token"]
```

### No Refresh Token Handling

Client credentials flow doesn't use refresh tokens. When access token expires:

1. Plugin detects expiration via `expires_in` field
2. Acquires new access token directly
3. No refresh token exchange needed

### Provider Support

This flow works with:
- ✅ Azure Entra ID (formerly Azure AD)
- ✅ Google Cloud Identity Platform
- ✅ Keycloak
- ✅ Auth0
- ✅ Okta
- ✅ Any OAuth2-compliant provider

## Security Considerations

### Client Secret Storage

- Secrets stored in environment variables (not in code)
- Plugin reads secrets on startup only
- Secrets never logged or exposed in API responses
- See SECURITY.md for secure credential management

### Token Handling

- Tokens cached in memory only (not persisted)
- Automatic refresh before expiration
- Thread-safe token access
- Tokens not logged or exposed

## Future Extensions

If interactive flows become necessary:

1. Create separate plugin or extension
2. Use authorization code flow with PKCE
3. Implement proper redirect handling
4. Add user session management

Current plugin would remain as-is for service accounts.

## Review Date

This decision should be reviewed if:
- Orthanc adds built-in OAuth web UI
- User-delegated access becomes a requirement
- New OAuth2 grant types become standard

## References

- [OAuth 2.0 Client Credentials Grant](https://datatracker.ietf.org/doc/html/rfc6749#section-4.4)
- [Azure Entra ID Client Credentials Flow](https://learn.microsoft.com/en-us/entra/identity-platform/v2-oauth2-client-creds-grant-flow)
- [Google OAuth2 Service Accounts](https://developers.google.com/identity/protocols/oauth2/service-account)
- [DICOM Standard - Network Communication](https://dicom.nema.org/medical/dicom/current/output/chtml/part08/PS3.8.html)
