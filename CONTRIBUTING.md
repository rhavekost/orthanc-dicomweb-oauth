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
