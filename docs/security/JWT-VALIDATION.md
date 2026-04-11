# JWT Signature Validation

## Overview

The plugin validates JWT access tokens by verifying their signature against a public key. This prevents token tampering and ensures tokens were issued by a trusted authority.

## Configuration

Add JWT validation configuration to your server:

```json
{
  "DicomWebOAuth": {
    "Servers": {
      "my-server": {
        "TokenEndpoint": "https://auth.example.com/token",
        "ClientId": "my-client-id",
        "ClientSecret": "my-secret",

        "JWTPublicKey": "-----BEGIN PUBLIC KEY-----\nMIIBIjANBg...\n-----END PUBLIC KEY-----",
        "JWTAudience": "https://api.example.com",
        "JWTIssuer": "https://auth.example.com",
        "JWTAlgorithms": ["RS256"]
      }
    }
  }
}
```

## Configuration Fields

- **JWTPublicKey**: Public key in PEM format for signature verification
- **JWTAudience**: Expected audience claim (optional)
- **JWTIssuer**: Expected issuer claim (optional)
- **JWTAlgorithms**: Allowed signing algorithms (default: ["RS256"])

## Obtaining Public Keys

### Azure AD

```bash
# Get JWKS URI from OpenID configuration
curl https://login.microsoftonline.com/{tenant}/.well-known/openid-configuration

# Download public keys
curl https://login.microsoftonline.com/{tenant}/discovery/keys
```

Convert JWKS to PEM format using online tools or libraries.

### Keycloak

```bash
# Get realm public key
curl http://localhost:8080/auth/realms/{realm}
```

The public key is in the `public_key` field.

## Security Benefits

- **Prevents token tampering**: Modified tokens fail signature verification
- **Validates token issuer**: Ensures token from trusted authority
- **Checks expiration**: Rejects expired tokens
- **Validates audience**: Ensures token intended for this API

## Validation Process

1. Token acquired from OAuth provider
2. Signature verified using public key
3. Claims validated (aud, iss, exp, nbf)
4. Token cached only if validation passes

## Azure Provider: Automatic JWKS Validation

The Azure provider (`azure-ad`) automatically validates tokens using Azure's JWKS endpoint — no `JWTPublicKey` configuration required. It verifies:

- **Signature** (RS256) against Azure's published public keys
- **Expiration** (`exp` claim)
- **Audience** (`aud` claim) — see note below
- **Issuer** (`iss` claim) — see note below

### Audience Verification

Audience verification requires `Scope` to end in `/.default`:

```json
"Scope": "https://dicom.healthcareapis.azure.com/.default"
```

The `aud` claim in the token is the bare resource URL (e.g. `https://dicom.healthcareapis.azure.com`), derived by stripping the `/.default` suffix.

If `Scope` does not end in `/.default`, audience verification is **skipped** and a warning is logged at startup:

```
Azure JWT audience verification is disabled because Scope does not end in '/.default'.
Tokens for any Azure resource will pass validation.
```

### Common Tenant (`TenantId` not set)

If `TenantId` is not configured, the provider defaults to the `common` multi-tenant endpoint. Issuer verification is automatically disabled in this case because Azure tokens carry the real tenant GUID in the `iss` claim — not the literal string `common`. A warning is logged:

```
Azure OAuth using multi-tenant 'common' endpoint. Healthcare deployments should
specify a tenant_id for tenant-specific token validation.
```

For healthcare production deployments, always specify `TenantId`.

### Disabling Azure JWKS Validation

To disable Azure's automatic JWKS validation entirely (not recommended):

```json
"DisableJWTValidation": true
```

## Disabling Validation (Generic Providers)

JWT validation is optional for generic providers. If `JWTPublicKey` is not configured, tokens are not validated. This is **not recommended for production**.
