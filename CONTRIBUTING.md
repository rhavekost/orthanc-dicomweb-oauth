# Contributing to orthanc-dicomweb-oauth

Thank you for your interest in contributing! This document provides guidelines for contributing to this project.

## Contributor License Agreement (CLA)

### Do I Need to Sign?

**Currently optional.** We have a CLA available but are not requiring it yet. We may require it in the future for:
- Patent protection
- License flexibility
- Corporate contributions

### How to Sign

If you choose to sign the CLA now (recommended for regular contributors):

1. Read the [CLA](CLA.md)
2. Add this to your PR description:
   ```
   I agree to the terms of the Contributor License Agreement (CLA.md).
   ```
3. Add your name to the [CLA signatories list](CLA.md#cla-signatories)

### What the CLA Means

- ✅ You keep ownership of your contributions
- ✅ You grant the Project permission to use your contributions
- ✅ You confirm you have the right to contribute
- ✅ You provide patent protection to users

**It's friendly!** Read it at [CLA.md](CLA.md) - we've written it in plain English.

### Questions About the CLA?

Open an issue and we'll clarify. We want contributing to be easy, not scary.

---

## Code of Conduct

This project adheres to a code of professional conduct. By participating, you agree to:

- Be respectful and inclusive
- Accept constructive criticism gracefully
- Focus on what's best for the project and community
- Show empathy towards other contributors

## How to Contribute

### Reporting Bugs

Before creating a bug report:

1. Check the [existing issues](https://github.com/rhavekost/orthanc-dicomweb-oauth/issues)
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

1. Check existing [feature requests](https://github.com/rhavekost/orthanc-dicomweb-oauth/issues?q=is%3Aissue+label%3Aenhancement)
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
git clone https://github.com/rhavekost/orthanc-dicomweb-oauth.git
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
├── src/                                # Source code
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
│   │   └── aws.py                      # AWS provider (basic)
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
├── docs/                               # Documentation
├── docker/                             # Docker configurations
├── config-templates/                   # Provider-specific config templates
├── examples/                           # Usage examples
├── scripts/                            # Utility scripts
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

Follow our coding standards (see [CODING-STANDARDS.md](docs/CODING-STANDARDS.md)):

- **PEP 8**: Python style guide (88-character line limit)
- **Type hints**: Use type annotations (100% coverage required)
- **Docstrings**: Google-style docstrings for all public functions (92%+ coverage)
- **Tests**: Write tests for new features (TDD preferred)
- **Complexity**: Keep cyclomatic complexity low (< 5.0 average)

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

# Run specific checks
black src/ tests/           # Code formatting
flake8 src/ tests/          # Linting
mypy src/                   # Type checking (strict mode)
bandit -r src/              # Security checks
pylint src/                 # Comprehensive linting (9.0+ required)
```

### 5. Commit Changes

## Commit Standards

We follow [Conventional Commits](https://www.conventionalcommits.org/) format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:** feat, fix, docs, style, refactor, perf, test, chore, ci, security

**Examples:**
- `feat(token): add JWT signature validation`
- `fix(config): handle missing optional fields gracefully`
- `docs: add troubleshooting guide for Azure`
- `security: encrypt client secrets in memory (CVSS 7.8)`

See [Git Workflow Guide](docs/git-workflow.md) for complete details.

### Co-Authorship

When pair programming or using AI assistance, include co-authors:

```
git commit -m "feat: implement feature

Description here

Co-Authored-By: Developer Name <dev@example.com>
Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

**Quick Reference:**

```bash
git commit -m "feat: add JWT signature validation"
git commit -m "fix: correct token expiration calculation"
git commit -m "docs: update configuration examples"
git commit -m "test: add integration tests for token refresh"
git commit -m "security: fix token exposure in logs (CVSS 9.1)"
```

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
- **CLA acknowledgment**: If you've signed the CLA

## Coding Standards

### Python Style

- **Line length**: 88 characters (Black default)
- **Imports**: Grouped (stdlib, third-party, local) and sorted with `isort`
- **Quotes**: Double quotes preferred
- **Type hints**: Required for all public functions (mypy strict mode)
- **Complexity**: Average cyclomatic complexity < 5.0 (currently 2.29)

Example:

```python
from typing import Dict, Optional

def parse_config(config_dict: Dict[str, Any]) -> Optional[ServerConfig]:
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

- **Docstrings**: Required for all public modules, classes, functions (Google style)
- **README**: Keep README.md up to date
- **Configuration docs**: Document all config options
- **Examples**: Provide working examples
- **ADRs**: Document significant architectural decisions in `docs/adr/`

## Pull Request Process

1. **CI/CD checks**: All automated checks must pass
   - Tests (pytest)
   - Code formatting (Black)
   - Import sorting (isort)
   - Linting (flake8, pylint 9.0+)
   - Type checking (mypy strict mode)
   - Security scanning (Bandit)
   - Docstring validation (pydocstyle)
   - Coverage reporting

2. **Code review**: At least one maintainer review required

3. **Documentation**: Update docs if behavior changes

4. **Changelog**: Entry will be added by maintainers

5. **Merge**: Squash and merge (maintainers will handle)

## Quality Standards

**Current Project Quality Score: A+ (97/100)**

Your contributions should maintain or improve:

- ✅ **100% type coverage** - All functions fully typed with mypy strict mode
- ✅ **92% docstring coverage** - Google-style docstrings on all public APIs
- ✅ **Low complexity** - Average cyclomatic complexity 2.29 (keep < 5.0)
- ✅ **Comprehensive linting** - pylint score 9.18/10 (minimum 9.0)
- ✅ **Pre-commit hooks** - All checks passing
- ✅ **CI/CD enforcement** - All quality checks enforced in GitHub Actions

**Quick quality check:**
```bash
./scripts/quality-check.sh
```

## Questions?

- **Documentation**: Check [docs/](docs/)
- **Coding Standards**: See [docs/CODING-STANDARDS.md](docs/CODING-STANDARDS.md)
- **Troubleshooting**: See [docs/troubleshooting.md](docs/troubleshooting.md)
- **Issues**: [GitHub Issues](https://github.com/rhavekost/orthanc-dicomweb-oauth/issues)
- **Discussions**: [GitHub Discussions](https://github.com/rhavekost/orthanc-dicomweb-oauth/discussions)

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (see [LICENSE](LICENSE)).

---

Thank you for contributing! 🎉
