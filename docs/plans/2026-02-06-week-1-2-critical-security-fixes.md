# Week 1-2 Critical Security Fixes & CI/CD Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix all critical security vulnerabilities (CVSS 8.9-9.3) and establish CI/CD pipeline to achieve 80+ security score within 2 weeks.

**Architecture:** Implement security hardening through token exposure removal, SSL verification, secure defaults, pre-commit hooks, and GitHub Actions CI/CD pipeline with automated security scanning.

**Tech Stack:** Python 3.11+, pytest, pre-commit, Black, flake8, mypy, Bandit, GitHub Actions, Docker

---

## PHASE 1: CRITICAL SECURITY FIXES (Days 1-2)

### Task 1: Remove Token Exposure from API (CV-1: CVSS 9.1)

**Priority:** CRITICAL
**Effort:** 30 minutes
**Impact:** Prevents token prefix leakage attacks

**Files:**
- Modify: `src/dicomweb_oauth_plugin.py:231`
- Test: `tests/test_monitoring_endpoints.py`

**Step 1: Write failing test for token privacy**

Add to `tests/test_monitoring_endpoints.py`:

```python
def test_status_endpoint_no_token_exposure(mock_plugin_with_config):
    """Test that status endpoint never exposes token content."""
    plugin = mock_plugin_with_config

    # Acquire token first
    plugin.token_managers["example-server"]._acquire_token()

    # Get status
    status = plugin.handle_rest_api_status()

    # Verify no token content is exposed
    assert "token_preview" not in status
    assert "token" not in status
    assert "access_token" not in status

    # Check servers status
    for server_name, server_status in status.get("servers", {}).items():
        assert "token_preview" not in server_status
        assert "token" not in server_status
        assert "access_token" not in server_status
        # Should only have boolean status
        assert "has_token" in server_status
        assert isinstance(server_status["has_token"], bool)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_monitoring_endpoints.py::test_status_endpoint_no_token_exposure -v`
Expected: FAIL with assertion error on "token_preview" key

**Step 3: Remove token exposure from status endpoint**

Modify `src/dicomweb_oauth_plugin.py`, find the `handle_rest_api_status()` method around line 220-240 and replace:

```python
# BEFORE (around line 231):
"token_preview": token[:20] + "..." if token else None,

# AFTER:
"has_token": token is not None,
```

Remove the entire `token_preview` line and replace with the boolean flag.

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_monitoring_endpoints.py::test_status_endpoint_no_token_exposure -v`
Expected: PASS

**Step 5: Run full test suite to check for regressions**

Run: `pytest tests/ -v`
Expected: All tests PASS

**Step 6: Commit**

```bash
git add src/dicomweb_oauth_plugin.py tests/test_monitoring_endpoints.py
git commit -m "security: remove token exposure from API endpoints (CV-1 CVSS 9.1)

- Replace token_preview with has_token boolean flag
- Prevents token prefix leakage attacks
- Add test coverage for token privacy

BREAKING CHANGE: status API no longer returns token_preview field

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

### Task 2: Add Explicit SSL/TLS Verification (CV-2: CVSS 9.3)

**Priority:** CRITICAL
**Effort:** 1 hour
**Impact:** Prevents MITM attacks on token acquisition

**Files:**
- Modify: `src/token_manager.py:109`
- Modify: `src/config_parser.py`
- Test: `tests/test_token_manager.py`

**Step 1: Write failing test for SSL verification**

Add to `tests/test_token_manager.py`:

```python
def test_ssl_verification_enabled_by_default(mock_config):
    """Test that SSL verification is enabled by default."""
    import unittest.mock as mock

    manager = TokenManager(mock_config)

    with mock.patch("requests.post") as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "access_token": "test_token",
            "expires_in": 3600
        }

        manager._acquire_token()

        # Verify SSL verification was enabled
        call_kwargs = mock_post.call_args[1]
        assert "verify" in call_kwargs
        assert call_kwargs["verify"] is True


def test_ssl_verification_can_be_disabled_explicitly(mock_config):
    """Test that SSL verification can be disabled if explicitly configured."""
    mock_config["VerifySSL"] = False
    manager = TokenManager(mock_config)

    import unittest.mock as mock

    with mock.patch("requests.post") as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "access_token": "test_token",
            "expires_in": 3600
        }

        manager._acquire_token()

        # Verify SSL verification was disabled
        call_kwargs = mock_post.call_args[1]
        assert "verify" in call_kwargs
        assert call_kwargs["verify"] is False


def test_ssl_verification_with_custom_ca_bundle(mock_config):
    """Test that custom CA bundle path can be specified."""
    mock_config["VerifySSL"] = "/path/to/ca-bundle.crt"
    manager = TokenManager(mock_config)

    import unittest.mock as mock

    with mock.patch("requests.post") as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "access_token": "test_token",
            "expires_in": 3600
        }

        manager._acquire_token()

        # Verify custom CA bundle was used
        call_kwargs = mock_post.call_args[1]
        assert call_kwargs["verify"] == "/path/to/ca-bundle.crt"
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_token_manager.py::test_ssl_verification_enabled_by_default -v`
Expected: FAIL (verify parameter not passed)

**Step 3: Add SSL verification configuration to ConfigParser**

Modify `src/config_parser.py`, add SSL verification documentation and default:

In the `parse_oauth_config` method, after the existing server configuration parsing, add:

```python
# SSL/TLS Verification (defaults to True for security)
server_config["VerifySSL"] = server_dict.get("VerifySSL", True)
```

**Step 4: Implement SSL verification in TokenManager**

Modify `src/token_manager.py`, in the `__init__` method around line 35-50:

```python
self.verify_ssl = config.get("VerifySSL", True)
```

Then modify the `_acquire_token()` method around line 109:

```python
# BEFORE:
response = requests.post(
    self.token_endpoint,
    headers=headers,
    data=data,
    timeout=30,
)

# AFTER:
response = requests.post(
    self.token_endpoint,
    headers=headers,
    data=data,
    timeout=30,
    verify=self.verify_ssl,  # Explicit SSL verification
)
```

**Step 5: Run tests to verify they pass**

Run: `pytest tests/test_token_manager.py -k ssl_verification -v`
Expected: All 3 SSL verification tests PASS

**Step 6: Update documentation**

Add to `docs/configuration-reference.md` under the server configuration section:

```markdown
#### VerifySSL

**Type:** Boolean or String
**Default:** `true`
**Required:** No

Controls SSL/TLS certificate verification when connecting to the OAuth token endpoint.

**Options:**
- `true` (default): Verify SSL certificates using system CA bundle
- `false`: Disable SSL verification (⚠️ NOT RECOMMENDED for production)
- `"/path/to/ca-bundle.crt"`: Use custom CA certificate bundle

**Example:**
```json
{
  "DicomWebOAuth": {
    "Servers": {
      "production-server": {
        "VerifySSL": true
      },
      "dev-server-with-self-signed-cert": {
        "VerifySSL": "/etc/ssl/certs/company-ca.crt"
      }
    }
  }
}
```

**Security Warning:** Disabling SSL verification (`false`) makes connections vulnerable to man-in-the-middle attacks. Only use this for local development with self-signed certificates, and NEVER in production.
```

**Step 7: Run full test suite**

Run: `pytest tests/ -v --cov=src --cov-report=term-missing`
Expected: All tests PASS, coverage >= 77%

**Step 8: Commit**

```bash
git add src/token_manager.py src/config_parser.py tests/test_token_manager.py docs/configuration-reference.md
git commit -m "security: add explicit SSL/TLS verification (CV-2 CVSS 9.3)

- Enable SSL verification by default (verify=True)
- Add configurable VerifySSL option (true/false/path)
- Support custom CA certificate bundles
- Add comprehensive test coverage
- Update configuration documentation

Prevents MITM attacks on OAuth token acquisition

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

### Task 3: Secure Default Configuration (CV-3: CVSS 8.9)

**Priority:** CRITICAL
**Effort:** 1 hour
**Impact:** Enables authentication by default, prevents unrestricted PHI access

**Files:**
- Modify: `docker/orthanc.json`
- Create: `docker/orthanc-secure.json`
- Modify: `docker/README.md`
- Modify: `README.md`

**Step 1: Create secure default configuration**

Create `docker/orthanc-secure.json`:

```json
{
  "Name": "Orthanc DICOMweb OAuth Production",
  "HttpPort": 8042,
  "DicomPort": 4242,

  "RemoteAccessAllowed": true,
  "AuthenticationEnabled": true,
  "RegisteredUsers": {
    "admin": "CHANGE_THIS_PASSWORD_IMMEDIATELY"
  },

  "Plugins": [
    "/etc/orthanc/plugins/dicomweb_oauth_plugin.py"
  ],

  "DicomWeb": {
    "Enable": true,
    "Root": "/dicom-web/",
    "EnableWado": true,
    "WadoRoot": "/wado",
    "Ssl": true,
    "QidoCaseSensitive": false,
    "Host": "0.0.0.0",
    "Port": 8042
  },

  "DicomWebOAuth": {
    "Servers": {
      "production-server": {
        "Url": "https://dicom.example.com/v2/",
        "TokenEndpoint": "https://login.example.com/oauth2/token",
        "ClientId": "${OAUTH_CLIENT_ID}",
        "ClientSecret": "${OAUTH_CLIENT_SECRET}",
        "Scope": "https://dicom.example.com/.default",
        "TokenRefreshBufferSeconds": 300,
        "VerifySSL": true
      }
    }
  },

  "Verbosity": "default",
  "LogLevel": "default"
}
```

**Step 2: Update development configuration with security warning**

Modify `docker/orthanc.json` to add comments (note: JSON doesn't support comments, so add to README):

Keep existing content but change:

```json
  "RemoteAccessAllowed": true,
  "AuthenticationEnabled": true,
  "RegisteredUsers": {
    "orthanc": "orthanc"
  },
```

**Step 3: Update Docker README with security guidance**

Modify `docker/README.md`, add security section at the top:

```markdown
# Docker Configuration

## ⚠️ SECURITY WARNING

The default `orthanc.json` configuration is **FOR DEVELOPMENT ONLY** and has security features disabled for ease of testing.

**For production deployments:**
1. Use `orthanc-secure.json` as your base configuration
2. Enable authentication (`"AuthenticationEnabled": true`)
3. Change default passwords immediately
4. Enable SSL/TLS (`"Ssl": true`)
5. Review all security settings

**NEVER deploy the development configuration to production or any environment handling real patient data (PHI).**

## Configuration Files

### orthanc.json (Development)
- Authentication: ✅ Enabled (default credentials: orthanc/orthanc)
- Remote Access: Enabled
- SSL: Disabled
- Use for: Local development, testing only

### orthanc-secure.json (Production Template)
- Authentication: ✅ Enabled (must change password)
- Remote Access: Enabled with authentication
- SSL: ✅ Enabled
- Use for: Production deployments, staging environments

## Quick Start

[Rest of existing README content...]
```

**Step 4: Update main README with security warning**

Modify `README.md`, add security section after "Features":

```markdown
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
```

**Step 5: Commit secure defaults**

```bash
git add docker/orthanc.json docker/orthanc-secure.json docker/README.md README.md
git commit -m "security: enable authentication in default config (CV-3 CVSS 8.9)

- Enable AuthenticationEnabled: true by default
- Create orthanc-secure.json production template
- Add security warnings to README files
- Document secure configuration practices

Prevents unrestricted PHI access in default deployment

BREAKING CHANGE: Authentication now enabled by default
Default credentials: orthanc/orthanc (must change in production)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## PHASE 2: DOCUMENTATION & SECURITY POLICY (Day 3)

### Task 4: Create SECURITY.md

**Priority:** HIGH
**Effort:** 30 minutes
**Impact:** Establishes vulnerability reporting process

**Files:**
- Create: `SECURITY.md`

**Step 1: Create SECURITY.md file**

Create `SECURITY.md` in project root:

```markdown
# Security Policy

## Supported Versions

| Version | Supported          | Security Updates |
| ------- | ------------------ | ---------------- |
| 1.0.x   | :white_check_mark: | Yes              |
| < 1.0   | :x:                | No               |

## Known Security Issues

**Current Security Score: 62/100 (Grade D)**

We are actively working to improve the security posture of this project. See [Comprehensive Project Assessment](docs/comprehensive-project-assessment.md) for details.

### Critical Vulnerabilities Fixed (As of 2026-02-06)

- ✅ **CV-1**: Token exposure in API responses (CVSS 9.1) - Fixed in v1.0.1
- ✅ **CV-2**: Missing SSL/TLS verification (CVSS 9.3) - Fixed in v1.0.1
- ✅ **CV-3**: Insecure default configuration (CVSS 8.9) - Fixed in v1.0.1

### Known Issues (In Progress)

- ⚠️ **CV-4**: Client secrets stored in plaintext memory (CVSS 7.8) - Target: v1.1.0
- ⚠️ No JWT signature validation - Target: v1.1.0
- ⚠️ No rate limiting on token endpoints - Target: v1.1.0
- ⚠️ Insufficient security event logging - Target: v1.2.0

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability, please follow responsible disclosure:

### Where to Report

**DO NOT** open a public GitHub issue for security vulnerabilities.

Instead, report via:

1. **Email**: [Insert security contact email]
2. **Private Security Advisory**: Use GitHub's [private vulnerability reporting](https://github.com/[username]/orthanc-dicomweb-oauth/security/advisories/new)

### What to Include

Please provide:

- Description of the vulnerability
- Steps to reproduce the issue
- Potential impact (confidentiality, integrity, availability)
- Affected versions
- Suggested fix (if available)

### Response Timeline

- **Initial Response**: Within 48 hours
- **Severity Assessment**: Within 5 business days
- **Fix Timeline**:
  - Critical (CVSS 9.0-10.0): 7 days
  - High (CVSS 7.0-8.9): 30 days
  - Medium (CVSS 4.0-6.9): 90 days
  - Low (CVSS 0.1-3.9): Next release

### Disclosure Policy

- We will confirm receipt of your report within 48 hours
- We will provide regular updates on our progress
- We will credit you in the security advisory (unless you prefer anonymity)
- We request that you do not publicly disclose the issue until we've issued a fix

## Security Best Practices

### For Deployment

1. **Always enable authentication** in Orthanc configuration
2. **Never use default credentials** in production
3. **Store secrets securely** using environment variables or secret managers
4. **Enable SSL/TLS** for all OAuth endpoints
5. **Use secure defaults** from `docker/orthanc-secure.json`
6. **Monitor security logs** for suspicious activity
7. **Keep dependencies updated** using Dependabot alerts

### For Development

1. **Never commit secrets** to version control
2. **Use `.env` files** for local development (add to `.gitignore`)
3. **Review security changes** carefully in PRs
4. **Run security scans** before committing (`pre-commit run --all-files`)
5. **Test with production-like configurations** before deploying

## Security Roadmap

### Immediate (Completed)
- ✅ Remove token exposure from API
- ✅ Enable SSL/TLS verification
- ✅ Secure default configuration
- ✅ Create SECURITY.md

### Short-term (Month 1)
- [ ] Implement JWT signature validation
- [ ] Add rate limiting protection
- [ ] Implement comprehensive audit logging
- [ ] Secure memory for client secrets

### Medium-term (Months 2-3)
- [ ] HIPAA compliance documentation
- [ ] Third-party security audit
- [ ] Penetration testing
- [ ] Security certifications

## Dependencies

We use automated security scanning for dependencies:

- **Dependabot**: Automatic dependency updates
- **Bandit**: Python security linter
- **Safety**: Python dependency security checker

## Compliance

This plugin is being developed for use in healthcare environments with the following compliance goals:

- **HIPAA** (Health Insurance Portability and Accountability Act): Target Month 6
- **SOC 2 Type II**: Target Month 6+

**Current Status**: Not HIPAA compliant. See [Project Assessment](docs/comprehensive-project-assessment.md#5-security-62100--critical-issues) for details.

## Security Contacts

- Security Email: [Insert security contact email]
- Project Maintainer: [Insert maintainer contact]
- Security Advisory: https://github.com/[username]/orthanc-dicomweb-oauth/security/advisories

---

**Last Updated**: 2026-02-06
**Next Review**: 2026-03-06
```

**Step 2: Commit SECURITY.md**

```bash
git add SECURITY.md
git commit -m "docs: create SECURITY.md vulnerability reporting policy

- Add responsible disclosure process
- Document known security issues
- Establish response timelines
- Provide security best practices
- Outline compliance roadmap

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

### Task 5: Create CONTRIBUTING.md

**Priority:** MEDIUM
**Effort:** 1 hour
**Impact:** Enables community contributions

**Files:**
- Create: `CONTRIBUTING.md`

**Step 1: Create CONTRIBUTING.md file**

Create `CONTRIBUTING.md`:

```markdown
# Contributing to orthanc-dicomweb-oauth

Thank you for your interest in contributing! This document provides guidelines for contributing to this project.

## Code of Conduct

This project adheres to a code of professional conduct. By participating, you agree to:

- Be respectful and inclusive
- Accept constructive criticism gracefully
- Focus on what's best for the project and community
- Show empathy towards other contributors

## How to Contribute

### Reporting Bugs

Before creating a bug report:

1. Check the [existing issues](https://github.com/[username]/orthanc-dicomweb-oauth/issues)
2. Review [troubleshooting documentation](docs/troubleshooting.md)
3. Ensure you're using the latest version

When filing a bug report, include:

- **Description**: Clear description of the issue
- **Environment**: Python version, Orthanc version, OS
- **Configuration**: Sanitized configuration (remove secrets!)
- **Steps to reproduce**: Minimal steps to reproduce the issue
- **Expected behavior**: What you expected to happen
- **Actual behavior**: What actually happened
- **Logs**: Relevant log excerpts (sanitize tokens!)

### Suggesting Enhancements

Enhancement suggestions are welcome! Please:

1. Check existing [feature requests](https://github.com/[username]/orthanc-dicomweb-oauth/issues?q=is%3Aissue+label%3Aenhancement)
2. Describe the use case and benefit
3. Provide examples of how it would work
4. Consider implementation complexity

### Security Vulnerabilities

**DO NOT** report security vulnerabilities via public issues.

See [SECURITY.md](SECURITY.md) for responsible disclosure process.

## Development Setup

### Prerequisites

- Python 3.11 or higher
- Docker (for integration testing)
- Git

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/[username]/orthanc-dicomweb-oauth.git
cd orthanc-dicomweb-oauth

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run tests to verify setup
pytest tests/ -v
```

### Project Structure

```
orthanc-dicomweb-oauth/
├── src/                    # Source code
│   ├── config_parser.py    # Configuration parsing
│   ├── token_manager.py    # OAuth token management
│   └── dicomweb_oauth_plugin.py  # Main plugin
├── tests/                  # Test suite
├── docs/                   # Documentation
├── docker/                 # Docker configurations
└── README.md
```

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bugfix-name
```

Branch naming conventions:
- `feature/`: New features
- `fix/`: Bug fixes
- `docs/`: Documentation changes
- `test/`: Test improvements
- `refactor/`: Code refactoring
- `security/`: Security fixes

### 2. Write Code

Follow our coding standards:

- **PEP 8**: Python style guide (88-character line limit)
- **Type hints**: Use type annotations
- **Docstrings**: Google-style docstrings for all public functions
- **Tests**: Write tests for new features (TDD preferred)

### 3. Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=term-missing

# Run specific test file
pytest tests/test_token_manager.py -v

# Run specific test
pytest tests/test_token_manager.py::test_acquire_token_success -v
```

### 4. Run Code Quality Checks

Pre-commit hooks run automatically, but you can run manually:

```bash
# Run all pre-commit hooks
pre-commit run --all-files

# Run specific hooks
black src/ tests/           # Code formatting
flake8 src/ tests/          # Linting
mypy src/                   # Type checking
bandit -r src/              # Security checks
```

### 5. Commit Changes

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```bash
git commit -m "feat: add JWT signature validation"
git commit -m "fix: correct token expiration calculation"
git commit -m "docs: update configuration examples"
git commit -m "test: add integration tests for token refresh"
git commit -m "security: fix token exposure in logs (CVSS 9.1)"
```

Commit message format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `test`: Tests
- `refactor`: Code refactoring
- `security`: Security fix
- `perf`: Performance improvement
- `chore`: Build/tooling changes

### 6. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a PR on GitHub with:

- **Clear title**: Following conventional commits format
- **Description**: What changes were made and why
- **Testing**: How you tested the changes
- **Screenshots**: If UI changes (for documentation)
- **Breaking changes**: Clearly marked if applicable
- **Related issues**: Link to related issues

## Coding Standards

### Python Style

- **Line length**: 88 characters (Black default)
- **Imports**: Grouped (stdlib, third-party, local) and sorted with `isort`
- **Quotes**: Double quotes preferred
- **Type hints**: Required for all public functions

Example:

```python
from typing import Dict, Optional

def parse_config(config_dict: Dict[str, any]) -> Optional[ServerConfig]:
    """Parse OAuth server configuration.

    Args:
        config_dict: Raw configuration dictionary from JSON.

    Returns:
        Parsed ServerConfig object, or None if parsing fails.

    Raises:
        ConfigError: If required fields are missing.
    """
    # Implementation
```

### Testing Standards

- **Coverage**: Aim for 90%+ coverage
- **Test structure**: Arrange-Act-Assert pattern
- **Test naming**: `test_<function>_<scenario>_<expected_result>`
- **Fixtures**: Use pytest fixtures for common setup
- **Mocking**: Mock external dependencies (OAuth endpoints, etc.)

Example:

```python
def test_token_manager_acquire_token_success(mock_config):
    """Test successful token acquisition with valid credentials."""
    # Arrange
    manager = TokenManager(mock_config)

    # Act
    token = manager.get_token()

    # Assert
    assert token is not None
    assert len(token) > 0
```

### Documentation Standards

- **Docstrings**: Required for all public modules, classes, functions
- **README**: Keep README.md up to date
- **Configuration docs**: Document all config options
- **Examples**: Provide working examples

## Pull Request Process

1. **CI/CD checks**: All automated checks must pass
   - Tests (pytest)
   - Code formatting (Black)
   - Linting (flake8)
   - Type checking (mypy)
   - Security scanning (Bandit)
   - Coverage (minimum 77%)

2. **Code review**: At least one maintainer review required

3. **Documentation**: Update docs if behavior changes

4. **Changelog**: Entry will be added by maintainers

5. **Merge**: Squash and merge (maintainers will handle)

## Questions?

- **Documentation**: Check [docs/](docs/)
- **Troubleshooting**: See [docs/troubleshooting.md](docs/troubleshooting.md)
- **Issues**: [GitHub Issues](https://github.com/[username]/orthanc-dicomweb-oauth/issues)
- **Discussions**: [GitHub Discussions](https://github.com/[username]/orthanc-dicomweb-oauth/discussions)

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (see [LICENSE](LICENSE)).

---

Thank you for contributing! 🎉
```

**Step 2: Commit CONTRIBUTING.md**

```bash
git add CONTRIBUTING.md
git commit -m "docs: create CONTRIBUTING.md development guidelines

- Add development setup instructions
- Document coding standards and workflow
- Establish PR process and requirements
- Provide testing guidelines

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## PHASE 3: CODE QUALITY AUTOMATION (Days 4-5)

### Task 6: Setup Pre-Commit Hooks

**Priority:** HIGH
**Effort:** 1 hour
**Impact:** Automated code quality enforcement

**Files:**
- Create: `.pre-commit-config.yaml`
- Create: `pyproject.toml`
- Modify: `requirements-dev.txt`

**Step 1: Add pre-commit to development dependencies**

Modify `requirements-dev.txt`:

```txt
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-mock>=3.11.1
coverage>=7.3.0
pre-commit>=3.5.0
black>=23.11.0
flake8>=6.1.0
mypy>=1.7.0
bandit>=1.7.5
isort>=5.12.0
```

**Step 2: Create .pre-commit-config.yaml**

Create `.pre-commit-config.yaml`:

```yaml
# Pre-commit hooks for orthanc-dicomweb-oauth
# See https://pre-commit.com for more information

repos:
  # General file checks
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json
      - id: check-added-large-files
        args: ['--maxkb=500']
      - id: check-merge-conflict
      - id: detect-private-key
      - id: detect-aws-credentials
        args: ['--allow-missing-credentials']

  # Python code formatting
  - repo: https://github.com/psf/black
    rev: 23.11.0
    hooks:
      - id: black
        args: ['--line-length=88']

  # Python import sorting
  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: ['--profile=black', '--line-length=88']

  # Python linting
  - repo: https://github.com/pycqa/flake8
    rev: 6.1.0
    hooks:
      - id: flake8
        args: ['--max-line-length=88', '--extend-ignore=E203,W503']

  # Security checks
  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.5
    hooks:
      - id: bandit
        args: ['-c', 'pyproject.toml']
        additional_dependencies: ['bandit[toml]']

  # Type checking
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.1
    hooks:
      - id: mypy
        additional_dependencies: ['types-requests']
        args: ['--ignore-missing-imports', '--no-strict-optional']
```

**Step 3: Create pyproject.toml configuration**

Create `pyproject.toml`:

```toml
[tool.black]
line-length = 88
target-version = ['py311']
include = '\.pyi?$'
extend-exclude = '''
/(
  # directories
  \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | _build
  | buck-out
  | build
  | dist
)/
'''

[tool.isort]
profile = "black"
line_length = 88
multi_line_output = 3
include_trailing_comma = true
force_grid_wrap = 0
use_parentheses = true
ensure_newline_before_comments = true

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = false
ignore_missing_imports = true
no_strict_optional = true

[tool.bandit]
exclude_dirs = [
    "tests",
    ".venv",
    "venv"
]
skips = [
    "B101",  # assert_used (used in tests)
]

[tool.pytest.ini_options]
minversion = "7.0"
addopts = "-ra -q --strict-markers"
testpaths = [
    "tests",
]
python_files = "test_*.py"
python_classes = "Test*"
python_functions = "test_*"

[tool.coverage.run]
source = ["src"]
omit = [
    "tests/*",
    ".venv/*",
    "venv/*",
]

[tool.coverage.report]
precision = 2
show_missing = true
skip_covered = false
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
]
```

**Step 4: Install pre-commit hooks**

Run: `pip install -r requirements-dev.txt && pre-commit install`
Expected: "pre-commit installed at .git/hooks/pre-commit"

**Step 5: Run pre-commit on all files**

Run: `pre-commit run --all-files`
Expected: All hooks pass (may auto-fix formatting issues)

**Step 6: Commit configuration**

```bash
git add .pre-commit-config.yaml pyproject.toml requirements-dev.txt
git commit -m "chore: add pre-commit hooks for code quality

- Configure Black for code formatting (88-char lines)
- Add isort for import sorting
- Configure flake8 for linting
- Add Bandit for security scanning
- Configure mypy for type checking
- Add general file checks

Enforces code quality standards automatically

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

### Task 7: Add Type Hints to Missing Functions

**Priority:** MEDIUM
**Effort:** 2 hours
**Impact:** Improves code maintainability and catches type errors

**Files:**
- Modify: `src/dicomweb_oauth_plugin.py`

**Step 1: Add type hints to REST API handlers**

Modify `src/dicomweb_oauth_plugin.py`, add imports at top:

```python
from typing import Dict, List, Optional, Tuple, Any
```

Then add type hints to REST API handler functions (around lines 200-280):

```python
def handle_rest_api_status(self) -> Dict[str, Any]:
    """Return plugin and token status for all configured servers.

    Returns:
        Dictionary containing plugin status and server information.
    """
    # ... existing implementation

def handle_rest_api_servers(self) -> Dict[str, Any]:
    """Return list of configured OAuth servers.

    Returns:
        Dictionary containing list of configured server names.
    """
    # ... existing implementation

def handle_rest_api_test_server(
    self, server_name: str
) -> Tuple[int, Dict[str, Any]]:
    """Test OAuth token acquisition for a specific server.

    Args:
        server_name: Name of the OAuth server to test.

    Returns:
        Tuple of (HTTP status code, response dictionary).
    """
    # ... existing implementation
```

**Step 2: Run mypy to check for type errors**

Run: `mypy src/ --ignore-missing-imports`
Expected: No errors (or minimal errors to fix)

**Step 3: Run tests to ensure no regressions**

Run: `pytest tests/ -v`
Expected: All tests PASS

**Step 4: Commit type hints**

```bash
git add src/dicomweb_oauth_plugin.py
git commit -m "refactor: add type hints to REST API handlers

- Add type hints to handle_rest_api_status
- Add type hints to handle_rest_api_servers
- Add type hints to handle_rest_api_test_server
- Improve code documentation and type safety

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## PHASE 4: CI/CD PIPELINE (Days 6-8)

### Task 8: Create GitHub Actions Workflow

**Priority:** CRITICAL
**Effort:** 2 days
**Impact:** Automated testing, security scanning, Docker builds

**Files:**
- Create: `.github/workflows/ci.yml`
- Create: `.github/workflows/security.yml`
- Create: `.github/workflows/docker.yml`
- Create: `.github/dependabot.yml`

**Step 1: Create CI workflow for tests and code quality**

Create `.github/workflows/ci.yml`:

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    name: Test Python ${{ matrix.python-version }}
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.11", "3.12"]

    steps:
      - name: Check out code
        uses: actions/checkout@v4

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: 'pip'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Run pre-commit hooks
        run: |
          pre-commit run --all-files

      - name: Run tests with coverage
        run: |
          pytest tests/ -v --cov=src --cov-report=xml --cov-report=term-missing

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v4
        with:
          file: ./coverage.xml
          fail_ci_if_error: false

      - name: Check coverage threshold
        run: |
          coverage report --fail-under=77

  lint:
    name: Lint and Type Check
    runs-on: ubuntu-latest

    steps:
      - name: Check out code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: 'pip'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements-dev.txt

      - name: Run Black
        run: black --check src/ tests/

      - name: Run isort
        run: isort --check-only src/ tests/

      - name: Run flake8
        run: flake8 src/ tests/

      - name: Run mypy
        run: mypy src/ --ignore-missing-imports
```

**Step 2: Create security scanning workflow**

Create `.github/workflows/security.yml`:

```yaml
name: Security

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  schedule:
    # Run weekly on Monday at 00:00 UTC
    - cron: '0 0 * * 1'

jobs:
  bandit:
    name: Bandit Security Scan
    runs-on: ubuntu-latest

    steps:
      - name: Check out code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install Bandit
        run: pip install bandit[toml]

      - name: Run Bandit
        run: bandit -r src/ -c pyproject.toml -f json -o bandit-report.json

      - name: Upload Bandit report
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: bandit-report
          path: bandit-report.json

  safety:
    name: Safety Dependency Check
    runs-on: ubuntu-latest

    steps:
      - name: Check out code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install Safety
        run: pip install safety

      - name: Run Safety check
        run: safety check --file requirements.txt --json --output safety-report.json || true

      - name: Upload Safety report
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: safety-report
          path: safety-report.json

  codeql:
    name: CodeQL Analysis
    runs-on: ubuntu-latest
    permissions:
      security-events: write
      actions: read
      contents: read

    steps:
      - name: Check out code
        uses: actions/checkout@v4

      - name: Initialize CodeQL
        uses: github/codeql-action/init@v3
        with:
          languages: python

      - name: Perform CodeQL Analysis
        uses: github/codeql-action/analyze@v3
```

**Step 3: Create Docker build workflow**

Create `.github/workflows/docker.yml`:

```yaml
name: Docker

on:
  push:
    branches: [main]
    tags: ['v*']
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  build:
    name: Build and Test Docker Image
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
      - name: Check out code
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to Container Registry
        if: github.event_name != 'pull_request'
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=ref,event=branch
            type=ref,event=pr
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=semver,pattern={{major}}
            type=sha

      - name: Build Docker image
        uses: docker/build-push-action@v5
        with:
          context: .
          push: false
          load: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
          platforms: linux/amd64

      - name: Test Docker image
        run: |
          docker run --rm ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }} python -c "import src.dicomweb_oauth_plugin; print('Plugin loaded successfully')"

      - name: Push Docker image
        if: github.event_name != 'pull_request'
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
          platforms: linux/amd64

  scan:
    name: Security Scan Docker Image
    runs-on: ubuntu-latest
    needs: build
    if: github.event_name != 'pull_request'

    steps:
      - name: Check out code
        uses: actions/checkout@v4

      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
          format: 'sarif'
          output: 'trivy-results.sarif'

      - name: Upload Trivy results to GitHub Security
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: 'trivy-results.sarif'
```

**Step 4: Create Dependabot configuration**

Create `.github/dependabot.yml`:

```yaml
version: 2
updates:
  # Python dependencies
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
      day: "monday"
    open-pull-requests-limit: 10
    reviewers:
      - "[your-github-username]"
    labels:
      - "dependencies"
      - "python"

  # GitHub Actions
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
      day: "monday"
    open-pull-requests-limit: 5
    reviewers:
      - "[your-github-username]"
    labels:
      - "dependencies"
      - "github-actions"

  # Docker
  - package-ecosystem: "docker"
    directory: "/docker"
    schedule:
      interval: "weekly"
      day: "monday"
    open-pull-requests-limit: 5
    reviewers:
      - "[your-github-username]"
    labels:
      - "dependencies"
      - "docker"
```

**Step 5: Create GitHub workflow directories**

Run: `mkdir -p .github/workflows`
Expected: Directory created

**Step 6: Commit CI/CD configuration**

```bash
git add .github/
git commit -m "ci: add GitHub Actions CI/CD pipeline

- Add CI workflow with Python 3.11/3.12 testing
- Add security scanning (Bandit, Safety, CodeQL)
- Add Docker build and vulnerability scanning (Trivy)
- Configure Dependabot for automated dependency updates
- Enforce 77% test coverage requirement

Implements automated testing and security scanning

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

### Task 9: Create Integration Test Script

**Priority:** MEDIUM
**Effort:** 2 hours
**Impact:** Validates end-to-end functionality

**Files:**
- Create: `scripts/integration-test.sh`
- Modify: `.github/workflows/ci.yml`

**Step 1: Create integration test script**

Create `scripts/integration-test.sh`:

```bash
#!/bin/bash
# Integration test script for orthanc-dicomweb-oauth
# Tests the plugin with a real Orthanc instance

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Orthanc DICOMweb OAuth Integration Test ===${NC}"

# Check prerequisites
command -v docker >/dev/null 2>&1 || {
    echo -e "${RED}Error: docker is required but not installed${NC}" >&2
    exit 1
}

command -v curl >/dev/null 2>&1 || {
    echo -e "${RED}Error: curl is required but not installed${NC}" >&2
    exit 1
}

# Configuration
ORTHANC_PORT=8042
CONTAINER_NAME="orthanc-oauth-integration-test"
MAX_WAIT=30

# Cleanup function
cleanup() {
    echo -e "${YELLOW}Cleaning up...${NC}"
    docker stop $CONTAINER_NAME >/dev/null 2>&1 || true
    docker rm $CONTAINER_NAME >/dev/null 2>&1 || true
}

# Register cleanup on exit
trap cleanup EXIT

# Stop any existing container
cleanup

echo -e "${YELLOW}Step 1: Building Docker image...${NC}"
docker build -t orthanc-oauth-test:latest .

echo -e "${YELLOW}Step 2: Starting Orthanc container...${NC}"
docker run -d \
    --name $CONTAINER_NAME \
    -p $ORTHANC_PORT:8042 \
    -e OAUTH_CLIENT_ID=test-client \
    -e OAUTH_CLIENT_SECRET=test-secret \
    orthanc-oauth-test:latest

echo -e "${YELLOW}Step 3: Waiting for Orthanc to be ready...${NC}"
WAITED=0
while ! curl -s -u orthanc:orthanc http://localhost:$ORTHANC_PORT/app/explorer.html >/dev/null; do
    if [ $WAITED -ge $MAX_WAIT ]; then
        echo -e "${RED}Error: Orthanc failed to start within ${MAX_WAIT}s${NC}"
        docker logs $CONTAINER_NAME
        exit 1
    fi
    echo -n "."
    sleep 1
    WAITED=$((WAITED + 1))
done
echo -e " ${GREEN}Ready!${NC}"

echo -e "${YELLOW}Step 4: Testing plugin REST API endpoints...${NC}"

# Test /oauth/status endpoint
echo -n "  - Testing /oauth/status... "
STATUS_RESPONSE=$(curl -s -u orthanc:orthanc http://localhost:$ORTHANC_PORT/oauth/status)
if echo "$STATUS_RESPONSE" | grep -q '"plugin_loaded"'; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
    echo "Response: $STATUS_RESPONSE"
    exit 1
fi

# Test /oauth/servers endpoint
echo -n "  - Testing /oauth/servers... "
SERVERS_RESPONSE=$(curl -s -u orthanc:orthanc http://localhost:$ORTHANC_PORT/oauth/servers)
if echo "$SERVERS_RESPONSE" | grep -q '"servers"'; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
    echo "Response: $SERVERS_RESPONSE"
    exit 1
fi

# Verify token preview is NOT exposed (security fix)
echo -n "  - Verifying token privacy... "
if echo "$STATUS_RESPONSE" | grep -q 'token_preview'; then
    echo -e "${RED}✗ SECURITY ISSUE: token_preview found in response${NC}"
    exit 1
else
    echo -e "${GREEN}✓${NC}"
fi

echo -e "${YELLOW}Step 5: Checking plugin logs...${NC}"
docker logs $CONTAINER_NAME 2>&1 | tail -20

echo -e "${GREEN}=== All integration tests passed! ===${NC}"
exit 0
```

**Step 2: Make script executable**

Run: `chmod +x scripts/integration-test.sh`
Expected: Script is now executable

**Step 3: Add integration test to CI workflow**

Add to `.github/workflows/ci.yml` after the test job:

```yaml
  integration:
    name: Integration Tests
    runs-on: ubuntu-latest
    needs: test

    steps:
      - name: Check out code
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Run integration tests
        run: ./scripts/integration-test.sh

      - name: Upload logs on failure
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: integration-test-logs
          path: |
            /tmp/orthanc-*.log
```

**Step 4: Test integration script locally**

Run: `./scripts/integration-test.sh`
Expected: All tests pass

**Step 5: Commit integration test**

```bash
git add scripts/integration-test.sh .github/workflows/ci.yml
git commit -m "test: add integration test script and CI job

- Create bash script for end-to-end testing
- Test plugin loading and REST API endpoints
- Verify token privacy (no token_preview exposure)
- Add integration test job to CI workflow
- Include Docker log upload on failure

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## PHASE 5: DOCUMENTATION UPDATES (Day 9)

### Task 10: Update README with Security Section

**Priority:** MEDIUM
**Effort:** 30 minutes
**Impact:** Informs users of security improvements

**Files:**
- Modify: `README.md`

**Step 1: Update README security section**

This was already done in Task 3, but let's add CI badges at the top of README.md:

Add after the title in `README.md`:

```markdown
# Orthanc DICOMweb OAuth Plugin

[![CI](https://github.com/[username]/orthanc-dicomweb-oauth/actions/workflows/ci.yml/badge.svg)](https://github.com/[username]/orthanc-dicomweb-oauth/actions/workflows/ci.yml)
[![Security](https://github.com/[username]/orthanc-dicomweb-oauth/actions/workflows/security.yml/badge.svg)](https://github.com/[username]/orthanc-dicomweb-oauth/actions/workflows/security.yml)
[![codecov](https://codecov.io/gh/[username]/orthanc-dicomweb-oauth/branch/main/graph/badge.svg)](https://codecov.io/gh/[username]/orthanc-dicomweb-oauth)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

[Rest of README...]
```

**Step 2: Commit README updates**

```bash
git add README.md
git commit -m "docs: add CI/CD and security badges to README

- Add CI workflow status badge
- Add Security workflow status badge
- Add Codecov coverage badge
- Add license badge

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

### Task 11: Create CHANGELOG.md

**Priority:** MEDIUM
**Effort:** 30 minutes
**Impact:** Documents version history and changes

**Files:**
- Create: `CHANGELOG.md`

**Step 1: Create CHANGELOG.md**

Create `CHANGELOG.md`:

```markdown
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
```

**Step 2: Commit CHANGELOG.md**

```bash
git add CHANGELOG.md
git commit -m "docs: create CHANGELOG.md

- Document all changes since v1.0.0
- Follow Keep a Changelog format
- Track security fixes and breaking changes

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## COMPLETION CHECKLIST

### Security Fixes ✅
- [x] Remove token previews from API (CV-1 CVSS 9.1)
- [x] Add SSL/TLS verification (CV-2 CVSS 9.3)
- [x] Enable authentication by default (CV-3 CVSS 8.9)

### Documentation ✅
- [x] Create SECURITY.md
- [x] Create CONTRIBUTING.md
- [x] Create CHANGELOG.md
- [x] Update README with security warnings
- [x] Document VerifySSL configuration

### Code Quality ✅
- [x] Add pre-commit hooks
- [x] Configure Black, isort, flake8, mypy
- [x] Add type hints to REST API handlers
- [x] Create pyproject.toml configuration

### CI/CD ✅
- [x] Create GitHub Actions CI workflow
- [x] Create security scanning workflow
- [x] Create Docker build workflow
- [x] Configure Dependabot
- [x] Add integration test script

### Testing ✅
- [x] Add test for token privacy
- [x] Add tests for SSL verification
- [x] Maintain 77%+ test coverage
- [x] Add integration tests

---

## EXPECTED OUTCOMES

### Security Score Improvement
- **Before**: 62/100 (Grade D)
- **After**: 82-85/100 (Grade B)
- **Improvement**: +20-23 points

### Specific Improvements
1. **Critical Vulnerabilities**: 0 (down from 3)
2. **SSL/TLS**: Enabled and verified
3. **Authentication**: Enabled by default
4. **Token Exposure**: Eliminated
5. **CI/CD Pipeline**: Full automation
6. **Test Coverage**: Maintained at 77%+
7. **Code Quality**: Automated enforcement

### Production Readiness
- **Was**: Development/POC only
- **Now**: Ready for staging environments
- **Next**: HIPAA compliance (Months 2-3)

---

## NEXT STEPS (Week 3-4)

After completing this plan, proceed with:

1. **JWT Signature Validation** (1-2 days)
2. **Rate Limiting** (1 day)
3. **Audit Logging** (1 day)
4. **Increase Test Coverage to 90%** (2-3 days)
5. **Performance Benchmarking** (1 day)

See [comprehensive-project-assessment.md](comprehensive-project-assessment.md) for full roadmap.

---

**Plan created**: 2026-02-06
**Target completion**: 2026-02-20 (2 weeks)
**Estimated effort**: 20-30 hours
