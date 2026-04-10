# Orthanc DICOMweb OAuth Plugin

[![CI](https://github.com/rhavekost/orthanc-dicomweb-oauth/actions/workflows/ci.yml/badge.svg)](https://github.com/rhavekost/orthanc-dicomweb-oauth/actions/workflows/ci.yml)
[![Security](https://github.com/rhavekost/orthanc-dicomweb-oauth/actions/workflows/security.yml/badge.svg)](https://github.com/rhavekost/orthanc-dicomweb-oauth/actions/workflows/security.yml)
[![codecov](https://codecov.io/gh/rhavekost/orthanc-dicomweb-oauth/branch/main/graph/badge.svg)](https://codecov.io/gh/rhavekost/orthanc-dicomweb-oauth)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Enables Orthanc to transparently connect to OAuth2-protected DICOMweb servers through the standard UI. Automatically handles token acquisition, caching, and refresh for any OAuth2/OIDC provider—users simply click "Send to DICOMWeb server" as usual.

## Features

### Core OAuth2 Features
✅ **Generic OAuth2** - Designed to work with any OAuth2/OIDC provider; verified with Azure
✅ **Specialized Providers** - Built-in provider modules for Azure Entra ID (verified), Google Cloud Healthcare API, and AWS HealthImaging (both unverified)
✅ **Provider Auto-Detection** - Automatically detects provider type from token endpoint URL
✅ **Automatic Token Refresh** - Proactive refresh before expiration (configurable buffer)
✅ **Zero-Downtime** - Thread-safe token caching, no interruption to DICOMweb operations

### Security & Compliance
✅ **HIPAA Compliant** - Complete compliance documentation for healthcare deployments
✅ **JWT Signature Validation** - Verify token integrity and claims
✅ **Rate Limiting** - Prevent abuse with configurable request limits
✅ **Secrets Encryption** - Automatic encryption of secrets in memory
✅ **Security Event Logging** - Comprehensive audit trail for compliance
✅ **SSL/TLS Verification** - Certificate validation for all OAuth endpoints

### Resilience & Monitoring
✅ **Circuit Breaker** - Prevent cascading failures with automatic circuit opening
✅ **Configurable Retry** - Exponential, linear, or fixed backoff strategies
✅ **Prometheus Metrics** - Comprehensive monitoring with `/metrics` endpoint
✅ **Structured Logging** - JSON logging with correlation IDs for distributed tracing
✅ **Error Codes** - Structured error codes with troubleshooting guidance

### Enterprise Features
✅ **Distributed Caching** - Redis support for horizontal scaling
✅ **Configuration Validation** - JSON Schema validation with user-friendly error messages
✅ **Configuration Migration** - Automatic migration from older config versions
✅ **Environment Variables** - Secure credential management via `${VAR}` substitution

### Developer Experience
✅ **Easy Deployment** - Python plugin, no compilation required
✅ **Docker-Ready** - Works with `orthancteam/orthanc` images out of the box
✅ **Type Safety** - 100% type coverage with mypy strict mode
✅ **Comprehensive Tests** - High test coverage with quality enforcement
✅ **Pre-commit Hooks** - Automatic formatting and quality checks

## 🎯 Transparent OAuth Integration

**Send DICOM studies to OAuth-protected servers using the standard Orthanc UI.**

This plugin enables seamless integration with OAuth-protected DICOMweb endpoints. Users interact with Orthanc exactly as they normally would—click "Send to DICOMWeb server" and OAuth authentication happens transparently. No manual token management. No API calls. No workflow changes.

### How It Works

1. Configure DICOMweb server URL to point to local OAuth proxy
2. User selects study and clicks "Send to DICOMWeb server" in Orthanc Explorer 2
3. Plugin automatically:
   - Acquires OAuth token from provider (Azure AD, Google, etc.)
   - Caches token for reuse
   - Forwards DICOM data with Bearer token
   - Refreshes token when needed

### Verified Working With

- ✅ **Azure Health Data Services DICOM** - Full transparent integration (client credentials and managed identity)
- 🔬 **Google Cloud Healthcare API** - Code implemented, not yet tested
- 🔬 **AWS HealthImaging** - Code implemented, not yet tested
- 🔬 **Other OAuth2 providers** - Code implemented, not yet tested

### Example Configuration

```json
{
  "DicomWeb": {
    "Servers": {
      "azure-dicom": {
        "Url": "http://localhost:8042/oauth-dicom-web/servers/azure-dicom",
        "Username": "admin",
        "Password": "secret"
      }
    }
  },
  "DicomWebOAuth": {
    "Servers": {
      "azure-dicom": {
        "Url": "https://workspace.dicom.azurehealthcareapis.com/v1",
        "TokenEndpoint": "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token",
        "ClientId": "{client-id}",
        "ClientSecret": "{client-secret}",
        "Scope": "https://dicom.healthcareapis.azure.com/.default"
      }
    }
  }
}
```

**📘 Full Documentation:** See [Transparent OAuth Guide](examples/azure/quickstart/TRANSPARENT-OAUTH-GUIDE.md) for complete setup instructions, troubleshooting, and architecture details.

## ⚠️ Security Notice

**This plugin handles authentication credentials for healthcare systems containing Protected Health Information (PHI).**

### Before Production Deployment:

1. **Review Security Documentation**: Read [Security Best Practices](docs/security/README.md)
2. **Enable Authentication**: Set `"AuthenticationEnabled": true` in Orthanc configuration
3. **Secure Secrets**: Never commit credentials to version control
4. **Use SSL/TLS**: Enable certificate verification for all OAuth endpoints
5. **Review Configuration**: Use `docker/orthanc-secure.json` as production template
6. **Enable Audit Logging**: Configure comprehensive security event logging

**HIPAA Compliant:** Complete compliance documentation for healthcare deployments. See [HIPAA Compliance Guide](docs/compliance/HIPAA-COMPLIANCE.md).

See [SECURITY.md](SECURITY.md) for vulnerability reporting.

---

## Problem Solved

Orthanc's built-in DICOMweb plugin only supports HTTP Basic auth or static headers, which prevents integration with modern cloud DICOM services that require OAuth2. This plugin bridges that gap by handling OAuth2 authentication transparently, enabling Orthanc users to send studies to cloud providers through the standard UI:

- **Azure Health Data Services** (Microsoft Entra ID OAuth2) - Verified working
- **Google Cloud Healthcare API** - Code implemented, not yet tested
- **AWS HealthImaging** - Code implemented, not yet tested
- **Any DICOMweb server behind Keycloak, Auth0, Okta, etc.** - Code implemented, not yet tested

## Deployment Options

### Azure Quickstart (15 minutes)
Perfect for demos and testing. Single command deployment.

```bash
cd examples/azure/quickstart
./deploy.sh
```

**Features**: Public endpoints, client credentials, simple setup

[Quickstart Guide →](examples/azure/quickstart/README.md)

### Azure Production (20 minutes)
Production-ready with enterprise security patterns.

```bash
cd examples/azure/production
./deploy.sh
```

**Features**: VNet isolation, private endpoints, managed identity, zero secrets

[Production Guide →](examples/azure/production/README.md)

## Quick Start

### Option 1: Docker (New Orthanc Installation)

Pull the standalone image from Docker Hub — includes Orthanc + plugin ready to run:

```bash
docker run -d \
  -p 8042:8042 -p 4242:4242 \
  -e OAUTH_CLIENT_ID=your-client-id \
  -e OAUTH_CLIENT_SECRET=your-client-secret \
  rhavekost/orthanc-dicomweb-oauth:latest
```

Or mount your own `orthanc.json` for full configuration:

```bash
docker run -d \
  -p 8042:8042 -p 4242:4242 \
  -v /path/to/orthanc.json:/etc/orthanc/orthanc.json \
  rhavekost/orthanc-dicomweb-oauth:latest
```

### Option 2: Add to Existing Orthanc Docker Setup

Use the plugin-only image to layer the plugin into your existing Orthanc Dockerfile:

```dockerfile
FROM your-existing-orthanc-image

# Copy plugin files from the plugin-only image
COPY --from=rhavekost/orthanc-dicomweb-oauth:latest-plugin /plugin/src /etc/orthanc/plugins/src/
COPY --from=rhavekost/orthanc-dicomweb-oauth:latest-plugin /plugin/schemas /etc/orthanc/plugins/schemas/

ENV PYTHONPATH=/etc/orthanc/plugins
```

Or with Docker Compose, use an init container pattern:

```yaml
services:
  orthanc:
    image: jodogne/orthanc-python:latest
    volumes:
      - plugin-files:/etc/orthanc/plugins/plugin
    depends_on:
      plugin-init:
        condition: service_completed_successfully

  plugin-init:
    image: rhavekost/orthanc-dicomweb-oauth:latest-plugin
    command: ["sh", "-c", "cp -r /plugin/. /target/"]
    volumes:
      - plugin-files:/target

volumes:
  plugin-files:
```

### Option 3: Manual Install (Bare Metal)

1. Download the latest release zip from [GitHub Releases](https://github.com/rhavekost/orthanc-dicomweb-oauth/releases)
2. Extract and follow [INSTALL.md](INSTALL.md)

### Option 4: Clone and Build

```bash
git clone https://github.com/rhavekost/orthanc-dicomweb-oauth.git
cd orthanc-dicomweb-oauth/docker
cp .env.example .env
# Edit .env with your OAuth credentials
docker-compose up -d
```

## Configuration

### Basic Configuration

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
        "Scope": "https://dicom.example.com/.default"
      }
    }
  }
}
```

### Configuration with Provider Auto-Detection

The plugin automatically detects Azure, Google, and Keycloak providers:

```json
{
  "DicomWebOAuth": {
    "Servers": {
      "azure-dicom": {
        "Url": "https://workspace-dicom.dicom.azurehealthcareapis.com/v2/",
        "TokenEndpoint": "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token",
        "ClientId": "${AZURE_CLIENT_ID}",
        "ClientSecret": "${AZURE_CLIENT_SECRET}",
        "Scope": "https://dicom.healthcareapis.azure.com/.default"
        // ProviderType: "azure" is auto-detected from TokenEndpoint
      }
    }
  }
}
```

### Azure Managed Identity (Zero Secrets)

For Azure Container Apps or Azure VMs with managed identity enabled, no client credentials are needed:

```json
{
  "DicomWebOAuth": {
    "Servers": {
      "azure-dicom": {
        "Url": "https://workspace-dicom.dicom.azurehealthcareapis.com/v2/",
        "ProviderType": "azuremanagedidentity",
        "Scope": "https://dicom.healthcareapis.azure.com/.default"
      }
    }
  }
}
```

This uses `DefaultAzureCredential` from the Azure Identity SDK - no `TokenEndpoint`, `ClientId`, or `ClientSecret` required. See the [Production Deployment Guide](examples/azure/production/README.md) for a complete example.

### Full Configuration Example

```json
{
  "DicomWebOAuth": {
    "ConfigVersion": "2.0",
    "LogLevel": "INFO",
    "LogFile": "/var/log/orthanc/dicomweb-oauth.log",

    "RateLimitRequests": 100,
    "RateLimitWindowSeconds": 60,

    "CacheType": "redis",
    "RedisUrl": "redis://localhost:6379/0",

    "ResilienceConfig": {
      "CircuitBreakerEnabled": true,
      "CircuitBreakerFailureThreshold": 5,
      "CircuitBreakerTimeout": 60,
      "RetryStrategy": "exponential",
      "RetryMaxAttempts": 3
    },

    "Servers": {
      "my-server": {
        "Url": "https://dicom.example.com",
        "TokenEndpoint": "https://auth.example.com/token",
        "ClientId": "${OAUTH_CLIENT_ID}",
        "ClientSecret": "${OAUTH_CLIENT_SECRET}",
        "Scope": "dicomweb",
        "TokenRefreshBufferSeconds": 300,

        "JWTPublicKey": "-----BEGIN PUBLIC KEY-----\n...\n-----END PUBLIC KEY-----",
        "JWTAudience": "https://api.example.com",
        "JWTIssuer": "https://auth.example.com",

        "VerifySSL": true
      }
    }
  }
}
```

### Configuration Options

**Core Server Options:**

| Option | Required | Description | Default |
|--------|----------|-------------|---------|
| `Url` | Yes | DICOMweb server base URL | - |
| `TokenEndpoint` | Yes* | OAuth2 token endpoint | - |
| `ClientId` | Yes* | OAuth2 client ID | - |
| `ClientSecret` | Yes* | OAuth2 client secret | - |
| `Scope` | No | OAuth2 scope | `""` |
| `TokenRefreshBufferSeconds` | No | Refresh buffer (seconds) | `300` |
| `ProviderType` | No | Provider type (auto-detected) | `"auto"` |
| `VerifySSL` | No | Verify SSL certificates | `true` |

*\* Not required when `ProviderType` is `"azuremanagedidentity"`. Managed identity uses `DefaultAzureCredential` instead of client credentials.*

**JWT Validation Options:**

| Option | Required | Description |
|--------|----------|-------------|
| `JWTPublicKey` | No | Public key for JWT signature validation |
| `JWTAudience` | No | Expected JWT audience claim |
| `JWTIssuer` | No | Expected JWT issuer claim |

**Global Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `ConfigVersion` | Configuration schema version | `"2.0"` |
| `LogLevel` | Logging level (DEBUG, INFO, WARNING, ERROR) | `"INFO"` |
| `LogFile` | Log file path (optional) | None |
| `RateLimitRequests` | Max requests per window | Disabled |
| `RateLimitWindowSeconds` | Rate limit window size | `60` |
| `CacheType` | Cache type (`memory` or `redis`) | `"memory"` |
| `RedisUrl` | Redis connection URL | None |

**Resilience Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `CircuitBreakerEnabled` | Enable circuit breaker | `false` |
| `CircuitBreakerFailureThreshold` | Failures before opening | `5` |
| `CircuitBreakerTimeout` | Timeout before retry (seconds) | `60` |
| `RetryStrategy` | Retry strategy (`exponential`, `linear`, `fixed`) | `"exponential"` |
| `RetryMaxAttempts` | Maximum retry attempts | `3` |

See [Configuration Reference](docs/configuration-reference.md) for complete details.

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
    "RateLimitRequests": 100,
    "RateLimitWindowSeconds": 60,
    "Servers": { ... }
  }
}
```

See [docs/security/RATE-LIMITING.md](docs/security/RATE-LIMITING.md) for details.

### Secrets Encryption

Secrets are automatically encrypted in memory. See [docs/security/SECRETS-ENCRYPTION.md](docs/security/SECRETS-ENCRYPTION.md) for details.

### Security Logging

Security events are automatically logged with correlation IDs for tracing:
- Authentication failures
- Token validation failures
- Rate limit violations
- SSL/TLS failures
- Configuration errors

## Provider-Specific Guides

- **[Azure Health Data Services](docs/quickstart-azure.md)** - Complete setup guide for Azure Entra ID
- **[Keycloak/OIDC](docs/quickstart-keycloak.md)** - Keycloak configuration guide
- **[Provider Support Matrix](docs/PROVIDER-SUPPORT.md)** - Comprehensive guide to all supported providers
- **[Configuration Reference](docs/configuration-reference.md)** - Complete configuration documentation
- **[Troubleshooting](docs/troubleshooting.md)** - Common issues and solutions

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
- **[Distributed Caching](docs/operations/DISTRIBUTED-CACHING.md)** - Redis configuration for horizontal scaling
- **[Kubernetes Deployment](docs/operations/KUBERNETES-DEPLOYMENT.md)** - Kubernetes deployment guide
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

**GET /dicomweb-oauth/metrics** - Prometheus metrics
```bash
curl http://localhost:8042/dicomweb-oauth/metrics
```

## Resilience Features

The plugin includes advanced resilience patterns:

- **Circuit Breaker**: Prevent cascading failures by opening circuit after threshold
- **Configurable Retry**: Exponential, linear, or fixed backoff strategies
- **Metrics**: Prometheus endpoint for monitoring token acquisition and errors
- **Correlation IDs**: Distributed tracing support for request tracking

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
3. **Provider Detection**: Automatically detects provider type from token endpoint
4. **HTTP Interception**: Plugin registers an outgoing HTTP request filter
5. **Token Management**:
   - First request triggers token acquisition using detected provider
   - Token is cached (in-memory or Redis)
   - Automatic refresh before expiration
   - Exponential backoff retry on network errors
   - Circuit breaker prevents cascading failures
6. **Request Modification**: Authorization header injected into matching requests
7. **Monitoring**: Metrics and logs track all operations with correlation IDs

## Architecture

```
Orthanc → DICOMweb Request → Plugin HTTP Filter → Provider Factory
                                                    ↓
                                              [Auto-detect Provider]
                                                    ↓
                                         [Azure|Google|AWS|Generic]
                                                    ↓
                                              Token Manager
                                                    ↓
                                        [Check Cache: Memory/Redis]
                                                    ↓
                                        [Acquire/Refresh Token]
                                         (with Circuit Breaker)
                                                    ↓
                                        OAuth2 Provider ← ClientCredentials
                                                    ↓
                                        [Validate JWT (optional)]
                                                    ↓
                                        [Cache Token + Metrics]
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
│   ├── dicomweb_oauth_plugin.py       # Main plugin entry point
│   ├── token_manager.py                # OAuth2 token management
│   ├── config_parser.py                # Configuration parsing
│   ├── config_schema.py                # JSON Schema validation
│   ├── config_migration.py             # Configuration version migration
│   ├── http_client.py                  # HTTP client abstraction
│   ├── jwt_validator.py                # JWT signature validation
│   ├── rate_limiter.py                 # Rate limiting
│   ├── secrets_manager.py              # Secrets encryption
│   ├── structured_logger.py            # Structured logging with correlation IDs
│   ├── error_codes.py                  # Error code definitions
│   ├── plugin_context.py               # Plugin context management
│   ├── oauth_providers/                # OAuth provider implementations
│   │   ├── base.py                     # Base provider interface
│   │   ├── factory.py                  # Provider factory with auto-detection
│   │   ├── generic.py                  # Generic OAuth2 provider
│   │   ├── azure.py                    # Azure Entra ID provider
│   │   ├── google.py                   # Google Cloud provider
│   │   ├── aws.py                      # AWS provider (basic)
│   │   └── managed_identity.py         # Azure Managed Identity provider
│   ├── cache/                          # Cache implementations
│   │   ├── base.py                     # Cache interface
│   │   ├── memory_cache.py             # In-memory cache
│   │   └── redis_cache.py              # Redis distributed cache
│   ├── resilience/                     # Resilience patterns
│   │   ├── circuit_breaker.py          # Circuit breaker implementation
│   │   └── retry_strategy.py           # Retry strategies
│   └── metrics/                        # Metrics collection
│       └── prometheus.py               # Prometheus metrics exporter
├── tests/                              # Comprehensive test suite
├── docker/                             # Docker development environment
├── config-templates/                   # Provider-specific config templates
├── examples/                           # Usage examples
├── scripts/                            # Utility scripts
└── docs/                               # Documentation
```

### Coding Standards

- ✅ **100% type coverage** - All functions fully typed with mypy strict mode
- ✅ **92% docstring coverage** - Google-style docstrings on all public APIs
- ✅ **Low complexity** - Average cyclomatic complexity 2.29
- ✅ **Comprehensive linting** - pylint (9.18/10), flake8, bandit, vulture, radon
- ✅ **Pre-commit hooks** - Automatic formatting and quality checks
- ✅ **CI/CD enforcement** - All quality checks enforced in GitHub Actions

**Quick quality check:**
```bash
./scripts/quality-check.sh
```

See [CODING-STANDARDS.md](docs/CODING-STANDARDS.md) for complete standards and guidelines.

## Contributing

Contributions welcome! Please:
1. Read [CONTRIBUTING.md](CONTRIBUTING.md) and sign the [CLA](CLA.md)
2. Fork the repository
3. Create a feature branch
4. Add tests for new functionality
5. Ensure all tests and quality checks pass
6. Submit a pull request

## License

MIT License - See LICENSE file for details

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for release history and version information.

Current version: **2.1.0** (2026-02-07)

## Acknowledgments

Built with ❤️ for the medical imaging community. Special thanks to the Orthanc project for creating an excellent open-source PACS.
