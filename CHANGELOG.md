# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
