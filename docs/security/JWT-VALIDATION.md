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

## Disabling Validation

JWT validation is optional. If `JWTPublicKey` is not configured, tokens are not validated. This is **not recommended for production**.
