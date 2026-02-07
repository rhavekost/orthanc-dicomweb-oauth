# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Google Cloud Healthcare API OAuth provider** - Specialized provider with automatic token endpoint configuration and scope validation
- **AWS HealthImaging OAuth provider** - Basic implementation for AWS authentication (full Signature v4 pending)
- **Provider Support Documentation** (`docs/PROVIDER-SUPPORT.md`) - Comprehensive guide covering Azure, Google, AWS, Keycloak, Auth0, Okta with setup instructions and troubleshooting
- **OAuth Flows Guide** (`docs/OAUTH-FLOWS.md`) - User-friendly explanation of OAuth2 flows and why only client credentials is supported
- **Missing Features Documentation** (`docs/MISSING-FEATURES.md`) - Explicitly documents intentionally excluded features to prevent repeated requests
- **Maintainability Documentation** (`docs/MAINTAINABILITY.md`) - Code quality metrics, complexity tracking, and refactoring guidelines
- **Backup & Recovery Guide** (`docs/operations/BACKUP-RECOVERY.md`) - Complete backup/recovery procedures for Docker Compose and Kubernetes
- **Backup Scripts** - Automated backup/restore/verify scripts with GPG encryption and S3 upload support
- **Contributor License Agreement** (`CLA.md`) - Apache-style individual contributor agreement
- **Code Review Checklist** (`docs/development/CODE-REVIEW-CHECKLIST.md`) - Consistent code review standards
- **Refactoring Guide** (`docs/development/REFACTORING-GUIDE.md`) - Safe refactoring practices with complexity thresholds
- **Complexity Monitoring Workflow** (`.github/workflows/complexity-monitoring.yml`) - Automated complexity regression detection in CI

### Documentation
- Configuration templates for Google Cloud Healthcare API (`config-templates/google-healthcare-api.json`)
- Configuration template for AWS HealthImaging (`config-templates/aws-healthimaging.json`)
- Provider comparison matrix with auto-detection capabilities
- Provider-specific troubleshooting guides
- Updated README with comprehensive documentation links
- CLA section added to CONTRIBUTING.md

## [2.0.0] - 2026-02-07

### Added
- HTTP client abstraction for dependency injection and testability
- Correlation IDs for distributed tracing and request tracking
- Automatic secret redaction in logs (client_secret, api_key, password, tokens)
- JSON Schema validation for configuration with user-friendly error messages
- Configuration versioning and migration (v1.0 to v2.0)
- Log rotation with configurable size and backup count
- Comprehensive test suite with 28 new tests (84% code coverage)

### Changed
- **BREAKING**: OAuth providers now accept optional http_client parameter
- **BREAKING**: Configuration now supports ConfigVersion field (auto-migrated from v1.0)
- Structured logger enhanced with correlation IDs and secret redaction
- Configuration parser auto-migrates old configs to v2.0 format
- Structured logger supports optional file output with rotation

### Fixed
- SOLID Dependency Inversion Principle violation in OAuth providers
- Logging gaps: correlation IDs, secret leakage, log rotation
- Configuration management: validation, versioning

## [Previous Releases]

### Security
- Remove token exposure from API endpoints (CV-1 CVSS 9.1)
- Add explicit SSL/TLS certificate verification (CV-2 CVSS 9.3)
- Enable authentication in default configuration (CV-3 CVSS 8.9)

### Added
- Create SECURITY.md for vulnerability reporting
- Create CONTRIBUTING.md for development guidelines
- Add pre-commit hooks for automated code quality
- Add GitHub Actions CI/CD pipeline
- Add security scanning (Bandit, Safety, CodeQL)
- Add Docker build automation with Trivy scanning
- Add Dependabot for automated dependency updates
- Add integration test script
- Add type hints to REST API handlers

### Changed
- **BREAKING**: Status API no longer returns `token_preview` field
- **BREAKING**: Authentication now enabled by default (credentials: orthanc/orthanc)
- Replace token_preview with has_token boolean flag
- Update Docker configuration with secure defaults

### Documentation
- Add security warnings to README
- Create orthanc-secure.json production template
- Add Docker security guidance
- Document VerifySSL configuration option
- Add CI/CD status badges

## [1.0.0] - 2026-01-15

### Added
- Initial release
- OAuth 2.0 client credentials flow implementation
- Token caching and automatic refresh
- Multiple OAuth provider support
- REST API monitoring endpoints
- Docker support
- Comprehensive documentation

### Security
- Thread-safe token management
- Environment variable substitution for secrets
- Retry logic with exponential backoff

[Unreleased]: https://github.com/[username]/orthanc-dicomweb-oauth/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/[username]/orthanc-dicomweb-oauth/releases/tag/v1.0.0
