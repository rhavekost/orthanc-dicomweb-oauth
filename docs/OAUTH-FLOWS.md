# OAuth2 Flows: What's Supported and Why

## What This Plugin Supports

✅ **Client Credentials Flow** - Service-to-service authentication

This is the **only** OAuth2 flow this plugin implements.

## What This Means for You

### You CAN Use This Plugin If:

- ✅ Your OAuth provider supports client credentials flow
- ✅ You have a service account (client ID + secret)
- ✅ Your DICOMweb server accepts service account tokens
- ✅ You're connecting Orthanc (server) to a DICOMweb server (server-to-server)

### You CANNOT Use This Plugin If:

- ❌ You need user-interactive login (browser-based authentication)
- ❌ You need to authenticate individual users (not service accounts)
- ❌ Your OAuth provider only supports authorization code flow
- ❌ You need device code flow (rare in healthcare)

## Why Only Client Credentials?

### The Short Answer

**Orthanc is a server, not a user application.** It needs to connect to DICOMweb automatically without human interaction.

### The Detailed Answer

**1. DICOM Workflows Are Automatic**

When a CT scanner sends an image to Orthanc, Orthanc needs to:
1. Receive the image (DICOM C-STORE)
2. Immediately forward it to a cloud DICOMweb server
3. No time to ask a user to log in

**2. Servers Don't Have Users Present**

- Orthanc runs as a background service
- No web browser for login redirects
- No user to type credentials
- Needs to work 24/7 without supervision

**3. Healthcare Providers Support This**

All major healthcare cloud providers support client credentials:
- ✅ Azure Health Data Services (Microsoft Entra ID)
- ✅ Google Cloud Healthcare API (service accounts)
- ✅ AWS HealthImaging (OAuth2 client credentials)

**4. Simplicity and Security**

- Single authentication flow = less code = fewer bugs
- No need to manage sessions, redirects, PKCE, state parameters
- Easier to audit and secure

## What About Other OAuth Flows?

### Authorization Code Flow

**What it is:** User logs in via browser, gets redirected back to app

**Why not supported:**
- Requires web UI for login
- Needs redirect URIs
- User must be present
- Orthanc has no login UI

**When you'd need it:** User-facing DICOM viewer, not server-to-server

### Refresh Token Flow

**What it is:** Long-lived token that gets new access tokens

**Why not supported:**
- Client credentials flow doesn't use refresh tokens
- Access tokens are requested directly each time
- Simpler: one flow instead of two

**Provider behavior:** Azure, Google don't issue refresh tokens for client credentials

### Device Code Flow

**What it is:** User enters code on separate device to authenticate

**Why not supported:**
- Requires user interaction (same problem as authorization code)
- Rare in healthcare
- Not needed for server-to-server

**When you'd need it:** Medical devices without browsers (not typical DICOM scenario)

## What If I Need Interactive Login?

If you need users to log in interactively to access DICOM data, you need a different solution:

### Option 1: Use Orthanc's Built-in Authentication

Orthanc supports:
- HTTP Basic Auth
- Custom authentication plugins
- Reverse proxy authentication (Nginx, Apache)

### Option 2: Build a Separate Web Application

```
[User Browser]
    ↓ OAuth2 authorization code flow
[Your Web App]
    ↓ Session cookie
[Orthanc]
    ↓ HTTP Basic or API key
[DICOMweb Server]
```

### Option 3: Use a DICOM Viewer

Many DICOM viewers handle user authentication:
- OHIF Viewer (supports OAuth2)
- Orthanc Web Viewer (supports Orthanc auth)
- Commercial viewers

## Summary

| Flow | Supported | Use Case | Why Not Supported |
|------|-----------|----------|-------------------|
| **Client Credentials** | ✅ Yes | Service-to-service | Supported! |
| Authorization Code | ❌ No | User login | No web UI in Orthanc |
| Refresh Token | ❌ No | Long sessions | Not used with client credentials |
| Device Code | ❌ No | Limited devices | No use case in DICOM |
| Implicit | ❌ No | Browser apps | Deprecated (insecure) |
| Password Grant | ❌ No | Legacy | Deprecated (insecure) |

## Technical Details

For developers and architects, see:
- [Provider Support Documentation](PROVIDER-SUPPORT.md)
- [OAuth 2.0 RFC 6749](https://datatracker.ietf.org/doc/html/rfc6749)
- [Security Documentation](SECURITY.md)

## Questions?

If this doesn't meet your needs, please open an issue explaining your use case. We're happy to clarify or point you to alternative solutions.
