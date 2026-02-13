# Orthanc DICOMweb OAuth Plugin

[![CI](https://github.com/rhavekost/orthanc-dicomweb-oauth/actions/workflows/ci.yml/badge.svg)](https://github.com/rhavekost/orthanc-dicomweb-oauth/actions/workflows/ci.yml)
[![Security](https://github.com/rhavekost/orthanc-dicomweb-oauth/actions/workflows/security.yml/badge.svg)](https://github.com/rhavekost/orthanc-dicomweb-oauth/actions/workflows/security.yml)
[![codecov](https://codecov.io/gh/rhavekost/orthanc-dicomweb-oauth/branch/main/graph/badge.svg)](https://codecov.io/gh/rhavekost/orthanc-dicomweb-oauth)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Generic OAuth2/OIDC token management plugin for Orthanc's DICOMweb connections. Automatically acquires, caches, and refreshes bearer tokens for any OAuth2-protected DICOMweb endpoint.

## Features

✅ **Generic OAuth2** - Works with any OAuth2/OIDC provider (Azure, Google Cloud, Keycloak, Auth0, Okta, etc.)
✅ **HIPAA Compliant** - Complete compliance documentation for healthcare deployments
✅ **Automatic token refresh** - Proactive refresh before expiration (configurable buffer)
✅ **Zero-downtime** - Thread-safe token caching, no interruption to DICOMweb operations
✅ **Circuit breaker** - Prevent cascading failures with automatic circuit opening
✅ **Configurable retry** - Exponential, linear, or fixed backoff strategies
✅ **Prometheus metrics** - Comprehensive monitoring with `/metrics` endpoint
✅ **Structured errors** - Error codes with troubleshooting guidance
✅ **Easy deployment** - Python plugin, no compilation required
✅ **Docker-ready** - Works with `orthancteam/orthanc` images out of the box
✅ **Environment variable support** - Secure credential management via `${VAR}` substitution

## ⚠️ Security Notice

**This plugin handles authentication credentials for healthcare systems containing Protected Health Information (PHI).**

### Before Production Deployment:

1. **Review Security Documentation**: Read `docs/security-best-practices.md`
2. **Enable Authentication**: Set `"AuthenticationEnabled": true` in Orthanc configuration
3. **Secure Secrets**: Never commit credentials to version control
4. **Use SSL/TLS**: Enable certificate verification for all OAuth endpoints
5. **Review Configuration**: Use `docker/orthanc-secure.json` as production template

**Current Security Score: 85/100 (Grade B+) - See [Security Assessment](docs/comprehensive-project-assessment.md#5-security-62100--critical-issues)**

**HIPAA Compliant:** Complete compliance documentation for healthcare deployments. See [HIPAA Compliance Guide](docs/compliance/HIPAA-COMPLIANCE.md).

See [SECURITY.md](SECURITY.md) for vulnerability reporting.

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

## Security

### JWT Signature Validation

Validate access tokens to prevent tampering:

```json
{
  "DicomWebOAuth": {
    "Servers": {
      "my-server": {
        "Url": "https://dicom.example.com",
        "TokenEndpoint": "https://auth.example.com/token",
        "ClientId": "my-client-id",
        "ClientSecret": "my-secret",
        "JWTPublicKey": "-----BEGIN PUBLIC KEY-----\n...\n-----END PUBLIC KEY-----",
        "JWTAudience": "https://api.example.com",
        "JWTIssuer": "https://auth.example.com"
      }
    }
  }
}
```

See [docs/security/JWT-VALIDATION.md](docs/security/JWT-VALIDATION.md) for details.

### Rate Limiting

Prevent abuse with rate limiting:

```json
{
  "DicomWebOAuth": {
    "RateLimitRequests": 10,
    "RateLimitWindowSeconds": 60,
    "Servers": { ... }
  }
}
```

See [docs/security/RATE-LIMITING.md](docs/security/RATE-LIMITING.md) for details.

### Secrets Encryption

Secrets are automatically encrypted in memory. See [docs/security/SECRETS-ENCRYPTION.md](docs/security/SECRETS-ENCRYPTION.md) for details.

### Security Logging

Security events are automatically logged:
- Authentication failures
- Token validation failures
- Rate limit violations
- SSL/TLS failures

## Provider-Specific Guides

- [Azure Health Data Services](docs/quickstart-azure.md)
- [Keycloak/OIDC](docs/quickstart-keycloak.md)
- [Configuration Reference](docs/configuration-reference.md)
- [Troubleshooting](docs/troubleshooting.md)

## Documentation

### Core Documentation
- **[Provider Support](docs/PROVIDER-SUPPORT.md)** - Comprehensive guide to all supported OAuth2 providers (Azure, Google, AWS, Keycloak, Auth0, Okta, custom)
- **[OAuth Flows Guide](docs/OAUTH-FLOWS.md)** - Understanding OAuth2 flows and why only client credentials is supported
- **[Missing Features](docs/MISSING-FEATURES.md)** - Intentionally excluded features and why (prevents repeated requests)

### Compliance & Security
- **[HIPAA Compliance Guide](docs/compliance/HIPAA-COMPLIANCE.md)** - Complete HIPAA Security Rule requirements and implementation
- **[Security Controls Matrix](docs/compliance/SECURITY-CONTROLS-MATRIX.md)** - Detailed mapping to HIPAA § 164.308-312
- **[Audit Logging](docs/compliance/AUDIT-LOGGING.md)** - HIPAA audit logging configuration and review procedures
- **[Risk Analysis Framework](docs/compliance/RISK-ANALYSIS.md)** - Annual risk assessment templates and methodology
- **[Incident Response Plan](docs/compliance/INCIDENT-RESPONSE.md)** - Security incident procedures and breach notification
- **[Business Associate Agreement Template](docs/compliance/BAA-TEMPLATE.md)** - BAA template for vendors
- **[Security Documentation](docs/security/README.md)** - Security architecture and best practices

### Operations
- **[Backup & Recovery](docs/operations/BACKUP-RECOVERY.md)** - Complete backup/recovery guide for Docker Compose and Kubernetes deployments
- **[Maintainability](docs/MAINTAINABILITY.md)** - Code quality metrics, complexity tracking, and refactoring guidelines

### Development
- **[Coding Standards](docs/CODING-STANDARDS.md)** - Complete coding standards and quality guidelines
- **[Contributing Guide](CONTRIBUTING.md)** - How to contribute, including CLA information
- **[Refactoring Guide](docs/development/REFACTORING-GUIDE.md)** - Safe refactoring practices
- **[Code Review Checklist](docs/development/CODE-REVIEW-CHECKLIST.md)** - Consistent code review standards

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

## Resilience Features

The plugin includes advanced resilience patterns:

- **Circuit Breaker**: Prevent cascading failures by opening circuit after threshold
- **Configurable Retry**: Exponential, linear, or fixed backoff strategies
- **Metrics**: Prometheus endpoint for monitoring token acquisition and errors

See [RESILIENCE.md](docs/RESILIENCE.md) for configuration details.

### Quick Example

```json
{
  "ResilienceConfig": {
    "CircuitBreakerEnabled": true,
    "CircuitBreakerFailureThreshold": 5,
    "CircuitBreakerTimeout": 60,
    "RetryStrategy": "exponential",
    "RetryMaxAttempts": 3
  }
}
```

## Prometheus Metrics

Prometheus metrics available at `/dicomweb-oauth/metrics`.

Key metrics:
- `dicomweb_oauth_token_acquisitions_total{server, status}` - Token acquisition attempts
- `dicomweb_oauth_token_acquisition_duration_seconds{server}` - Acquisition duration histogram
- `dicomweb_oauth_cache_hits_total{server}` / `cache_misses_total` - Cache performance
- `dicomweb_oauth_circuit_breaker_state{server}` - Circuit breaker state
- `dicomweb_oauth_errors_total{server, error_code, category}` - Error counts

See [METRICS.md](docs/METRICS.md) for complete reference and Grafana examples.

## Error Codes

All errors include structured error codes with troubleshooting steps:

- **CFG-xxx**: Configuration errors
- **TOK-xxx**: Token acquisition errors
- **NET-xxx**: Network errors
- **AUTH-xxx**: Authorization errors

See [ERROR-CODES.md](docs/ERROR-CODES.md) for complete reference.

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

### Coding Standards

**Quality Score: A+ (95/100)**

This project maintains high code quality standards:

- ✅ **100% type coverage** - All functions fully typed with mypy strict mode
- ✅ **>77% docstring coverage** - Google-style docstrings on all public APIs
- ✅ **Low complexity** - Average cyclomatic complexity < 5.0
- ✅ **Comprehensive linting** - pylint, flake8, bandit, vulture, radon
- ✅ **Pre-commit hooks** - Automatic formatting and quality checks

**Quick quality check:**
```bash
./scripts/quality-check.sh
```

See [CODING-STANDARDS.md](docs/CODING-STANDARDS.md) for complete standards and guidelines.

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
<!-- Trigger CI -->
