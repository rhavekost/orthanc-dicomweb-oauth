# Orthanc DICOMweb OAuth Plugin

[![CI](https://github.com/[username]/orthanc-dicomweb-oauth/actions/workflows/ci.yml/badge.svg)](https://github.com/[username]/orthanc-dicomweb-oauth/actions/workflows/ci.yml)
[![Security](https://github.com/[username]/orthanc-dicomweb-oauth/actions/workflows/security.yml/badge.svg)](https://github.com/[username]/orthanc-dicomweb-oauth/actions/workflows/security.yml)
[![codecov](https://codecov.io/gh/[username]/orthanc-dicomweb-oauth/branch/main/graph/badge.svg)](https://codecov.io/gh/[username]/orthanc-dicomweb-oauth)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Generic OAuth2/OIDC token management plugin for Orthanc's DICOMweb connections. Automatically acquires, caches, and refreshes bearer tokens for any OAuth2-protected DICOMweb endpoint.

## Features

✅ **Generic OAuth2** - Works with any OAuth2/OIDC provider (Azure, Google Cloud, Keycloak, Auth0, Okta, etc.)
✅ **Automatic token refresh** - Proactive refresh before expiration (configurable buffer)
✅ **Zero-downtime** - Thread-safe token caching, no interruption to DICOMweb operations
✅ **Easy deployment** - Python plugin, no compilation required
✅ **Docker-ready** - Works with `orthancteam/orthanc` images out of the box
✅ **Environment variable support** - Secure credential management via `${VAR}` substitution
✅ **Monitoring endpoints** - REST API for status checks and testing
✅ **Retry logic** - Automatic retry with exponential backoff for network errors

## ⚠️ Security Notice

**This plugin handles authentication credentials for healthcare systems containing Protected Health Information (PHI).**

### Before Production Deployment:

1. **Review Security Documentation**: Read `docs/security-best-practices.md`
2. **Enable Authentication**: Set `"AuthenticationEnabled": true` in Orthanc configuration
3. **Secure Secrets**: Never commit credentials to version control
4. **Use SSL/TLS**: Enable certificate verification for all OAuth endpoints
5. **Review Configuration**: Use `docker/orthanc-secure.json` as production template

**Current Security Score: 62/100 (Grade D) - See [Security Assessment](docs/comprehensive-project-assessment.md#5-security-62100--critical-issues)**

Critical security improvements are in progress. See [SECURITY.md](SECURITY.md) for vulnerability reporting.

---

## Problem Solved

Orthanc's DICOMweb plugin only supports HTTP Basic auth or static headers. This plugin enables Orthanc to connect to any OAuth2-protected DICOMweb server:

- **Azure Health Data Services** (Microsoft Entra ID OAuth2)
- **Google Cloud Healthcare API**
- **AWS HealthImaging** (OAuth2)
- **Any DICOMweb server behind Keycloak, Auth0, Okta, etc.**

## Quick Start

### Docker (Recommended)

1. **Clone and configure:**
   ```bash
   git clone https://github.com/yourusername/orthanc-dicomweb-oauth.git
   cd orthanc-dicomweb-oauth/docker
   cp .env.example .env
   # Edit .env with your OAuth credentials
   ```

2. **Start Orthanc:**
   ```bash
   docker-compose up -d
   ```

3. **Test the connection:**
   ```bash
   curl http://localhost:8042/dicomweb-oauth/status
   ```

### Manual Installation

1. **Install dependencies:**
   ```bash
   pip install requests
   ```

2. **Copy plugin files to Orthanc:**
   ```bash
   cp src/*.py /etc/orthanc/plugins/
   ```

3. **Configure Orthanc** (see [Configuration](#configuration))

4. **Restart Orthanc**

## Configuration

Add to your `orthanc.json`:

```json
{
  "Plugins": [
    "/etc/orthanc/plugins/dicomweb_oauth_plugin.py"
  ],

  "DicomWebOAuth": {
    "Servers": {
      "my-cloud-dicom": {
        "Url": "https://dicom.example.com/v2/",
        "TokenEndpoint": "https://login.example.com/oauth2/token",
        "ClientId": "${OAUTH_CLIENT_ID}",
        "ClientSecret": "${OAUTH_CLIENT_SECRET}",
        "Scope": "https://dicom.example.com/.default",
        "TokenRefreshBufferSeconds": 300
      }
    }
  }
}
```

### Configuration Options

| Option | Required | Description | Default |
|--------|----------|-------------|---------|
| `Url` | Yes | DICOMweb server base URL | - |
| `TokenEndpoint` | Yes | OAuth2 token endpoint | - |
| `ClientId` | Yes | OAuth2 client ID | - |
| `ClientSecret` | Yes | OAuth2 client secret | - |
| `Scope` | No | OAuth2 scope | `""` |
| `TokenRefreshBufferSeconds` | No | Refresh buffer (seconds) | `300` |

### Environment Variables

Use `${VAR_NAME}` syntax in configuration for secure credential management:

```json
{
  "ClientId": "${OAUTH_CLIENT_ID}",
  "ClientSecret": "${OAUTH_CLIENT_SECRET}"
}
```

## Provider-Specific Guides

- [Azure Health Data Services](docs/quickstart-azure.md)
- [Keycloak/OIDC](docs/quickstart-keycloak.md)
- [Configuration Reference](docs/configuration-reference.md)
- [Troubleshooting](docs/troubleshooting.md)

## Monitoring & Testing

### REST API Endpoints

The plugin exposes monitoring endpoints:

**GET /dicomweb-oauth/status** - Plugin status
```bash
curl http://localhost:8042/dicomweb-oauth/status
```

**GET /dicomweb-oauth/servers** - List configured servers
```bash
curl http://localhost:8042/dicomweb-oauth/servers
```

**POST /dicomweb-oauth/servers/{name}/test** - Test token acquisition
```bash
curl -X POST http://localhost:8042/dicomweb-oauth/servers/my-cloud-dicom/test
```

## How It Works

1. **Plugin Registration**: Orthanc loads the Python plugin on startup
2. **Configuration**: Plugin reads OAuth settings from `orthanc.json`
3. **HTTP Interception**: Plugin registers an outgoing HTTP request filter
4. **Token Management**:
   - First request triggers token acquisition
   - Token is cached in memory
   - Automatic refresh before expiration
   - Exponential backoff retry on network errors
5. **Request Modification**: Authorization header injected into matching requests

## Architecture

```
Orthanc → DICOMweb Request → Plugin HTTP Filter → Token Manager
                                                    ↓
                                              [Check Cache]
                                                    ↓
                                           [Acquire/Refresh Token]
                                                    ↓
                                        OAuth2 Provider ← ClientCredentials
                                                    ↓
                                              [Cache Token]
                                                    ↓
                              Request + Authorization: Bearer <token>
                                                    ↓
                                            DICOMweb Server
```

## Development

### Running Tests

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

### Project Structure

```
orthanc-dicomweb-oauth/
├── src/
│   ├── dicomweb_oauth_plugin.py    # Main plugin entry point
│   ├── token_manager.py             # OAuth2 token management
│   └── config_parser.py             # Configuration parsing
├── tests/                           # Comprehensive test suite
├── docker/                          # Docker development environment
├── examples/                        # Provider-specific examples
└── docs/                            # Documentation
```

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - See LICENSE file for details

## Acknowledgments

Built with ❤️ for the medical imaging community. Special thanks to the Orthanc project for creating an excellent open-source PACS.
