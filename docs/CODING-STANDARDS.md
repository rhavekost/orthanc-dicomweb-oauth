# Coding Standards

This document defines the coding standards for the Orthanc DICOMweb OAuth Plugin project. All code must adhere to these standards to maintain high quality, readability, and maintainability.

## Quality Metrics

Our project maintains an **A+ (95/100)** coding standards score based on:

- **Type Safety**: 100% type hint coverage with mypy strict mode
- **Documentation**: >77% docstring coverage (Google style)
- **Code Quality**: Average cyclomatic complexity < 5.0
- **Testing**: Comprehensive test coverage with quality checks
- **Linting**: Multiple linting tools configured (pylint, flake8, bandit, etc.)

## Python Version

- **Minimum**: Python 3.11
- **Target**: Python 3.11

## Code Formatting

### Black

All Python code must be formatted with [Black](https://black.readthedocs.io/).

```bash
black src/ tests/
```

**Configuration** (`pyproject.toml`):
```toml
[tool.black]
line-length = 88
target-version = ['py311']
```

### Import Sorting (isort)

Imports must be sorted with [isort](https://pycqa.github.io/isort/) using Black-compatible settings.

```bash
isort src/ tests/
```

**Configuration** (`pyproject.toml`):
```toml
[tool.isort]
profile = "black"
line_length = 88
```

## Type Safety

### Type Hints (Required)

**All functions must have complete type annotations:**

```python
# ✅ CORRECT
def process_token(token: str, expiry: int) -> Dict[str, Any]:
    """Process token with expiry."""
    return {"token": token, "expires_in": expiry}

# ❌ INCORRECT
def process_token(token, expiry):
    return {"token": token, "expires_in": expiry}
```

**Rules:**
- All function parameters must have type hints (except `self`, `cls`)
- All functions must have return type annotations (use `-> None` for void)
- Use `Optional[Type]` for nullable values
- Use `Dict[str, Any]` for dictionaries with mixed values
- Use `Any` sparingly; prefer specific types

### Mypy (Strict Mode)

All code must pass mypy in **strict mode**.

```bash
mypy src/
```

**Configuration** (`pyproject.toml`):
```toml
[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

## Documentation

### Docstrings (Google Style)

All public functions, classes, and methods must have docstrings following [Google style](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings).

```python
def acquire_token(server_name: str, force_refresh: bool = False) -> OAuthToken:
    """
    Acquire OAuth token for a configured server.

    Args:
        server_name: Name of the OAuth server configuration
        force_refresh: Force token refresh even if cached token is valid

    Returns:
        OAuthToken with access_token and expiry information

    Raises:
        TokenAcquisitionError: If token acquisition fails
        ValueError: If server_name is not configured
    """
```

**Requirements:**
- Minimum docstring coverage: 77% overall
- Critical modules (plugin, token_manager, config_parser): 80%
- Docstrings must end with punctuation
- Args, Returns, Raises sections required for non-trivial functions

**Validation:**
```bash
pydocstyle --convention=google src/
```

## Code Quality

### Naming Conventions

**Variables and Functions:**
- `snake_case` for variables, functions, methods
- `UPPER_CASE` for module-level constants
- `_leading_underscore` for private/internal items

**Classes:**
- `PascalCase` for class names
- `_LeadingUnderscore` for internal classes

**Module Constants:**
```python
# ✅ CORRECT - Public API constant
API_VERSION = "1.0"

# ✅ CORRECT - Private implementation detail
_ORTHANC_AVAILABLE = True
_MAX_RETRIES = 3

# ❌ INCORRECT - Should be private
ORTHANC_AVAILABLE = True  # Implementation detail, not part of public API
```

### Magic Numbers

**Never use magic numbers.** Always define named constants.

```python
# ✅ CORRECT
MAX_TOKEN_ACQUISITION_RETRIES = 3
TOKEN_REQUEST_TIMEOUT_SECONDS = 30

def acquire_token(self) -> OAuthToken:
    for attempt in range(MAX_TOKEN_ACQUISITION_RETRIES):
        try:
            return self._fetch_token(timeout=TOKEN_REQUEST_TIMEOUT_SECONDS)
        except Exception:
            continue

# ❌ INCORRECT
def acquire_token(self) -> OAuthToken:
    for attempt in range(3):  # What does 3 mean?
        try:
            return self._fetch_token(timeout=30)  # What does 30 mean?
        except Exception:
            continue
```

### Cyclomatic Complexity

**Maximum complexity targets:**
- Average complexity: < 5.0 (Grade A)
- Individual functions: < 7 (Grade B or better)
- No functions with complexity >= 10 (Grade C or worse)

**Check complexity:**
```bash
radon cc src/ -a  # Show average
radon cc src/ -n C  # Show functions with complexity >= C
```

**If complexity is too high:**
1. Extract helper functions
2. Simplify conditional logic
3. Use early returns
4. Apply strategy pattern for complex branching

### Dead Code

**No unused code allowed.** Use vulture to detect dead code.

```bash
vulture src/ --min-confidence 80
```

**Handle required-but-unused parameters:**
```python
# ✅ CORRECT - Prefix with underscore for API-required params
def handle_rest_api(output: Any, uri: str, **_request: Any) -> None:
    """REST API handler (request dict unused but required by API)."""
    pass

def OnChange(_changeType: int, level: int, _resource: str) -> None:
    """Orthanc callback (some params required but unused)."""
    pass
```

## Linting

### Flake8

```bash
flake8 src/ tests/
```

**Configuration** (`.flake8`):
```ini
[flake8]
max-line-length = 88
extend-ignore = E203, W503
```

### Pylint

All code must score >= 9.0/10 on pylint.

```bash
pylint src/ --rcfile=pyproject.toml
```

**Configuration** (`pyproject.toml`):
```toml
[tool.pylint.main]
py-version = "3.11"

[tool.pylint.messages_control]
max-line-length = 88
disable = [
    "C0114",  # missing-module-docstring (handled by pydocstyle)
    "C0115",  # missing-class-docstring (handled by pydocstyle)
    "C0116",  # missing-function-docstring (handled by pydocstyle)
]
```

### Bandit (Security)

```bash
bandit -r src/
```

Security checks for common vulnerabilities.

## Testing

### Test Coverage

**Minimum test coverage: 80%**

```bash
pytest --cov=src --cov-report=html --cov-report=term
```

### Test Organization

```
tests/
├── test_<module_name>.py       # Unit tests
├── test_naming_conventions.py  # Naming standards
├── test_code_quality.py        # Magic numbers, complexity
├── test_type_coverage.py       # Type hint coverage
├── test_docstring_coverage.py  # Documentation coverage
├── test_tooling_config.py      # Tool configuration
└── test_linting_tools.py       # Linting verification
```

### Test Quality

```python
# ✅ CORRECT - Clear test name, docstring, assertions
def test_token_manager_caches_valid_tokens() -> None:
    """Token manager should return cached token if still valid."""
    manager = TokenManager(config)
    token1 = manager.get_token("server1")
    token2 = manager.get_token("server1")

    assert token1.access_token == token2.access_token
    assert mock_provider.acquire_token.call_count == 1
```

## Pre-commit Hooks

All code must pass pre-commit checks before committing.

**Install hooks:**
```bash
pre-commit install
```

**Pre-commit checks:**
1. Trim trailing whitespace
2. Fix end of files
3. Check YAML/JSON syntax
4. Check for large files
5. Detect private keys/AWS credentials
6. **Black** - Format code
7. **isort** - Sort imports
8. **flake8** - Linting
9. **bandit** - Security
10. **mypy** - Type checking

## Continuous Integration

All quality checks run automatically in CI:

```yaml
# .github/workflows/ci.yml
- name: Check code formatting
  run: black --check src/ tests/

- name: Check import sorting
  run: isort --check-only src/ tests/

- name: Run flake8
  run: flake8 src/ tests/

- name: Run mypy
  run: mypy src/

- name: Run pylint
  run: pylint src/

- name: Run bandit
  run: bandit -r src/

- name: Check complexity
  run: radon cc src/ -a --total-average

- name: Check dead code
  run: vulture src/ --min-confidence 80

- name: Run tests with coverage
  run: pytest --cov=src --cov-report=term --cov-fail-under=80
```

## Quality Check Script

Run all quality checks locally:

```bash
./scripts/quality-check.sh
```

This script runs:
1. Code formatting checks (black, isort)
2. Linting (flake8, pylint, bandit)
3. Type checking (mypy)
4. Complexity analysis (radon)
5. Dead code detection (vulture)
6. Test suite with coverage
7. Documentation checks (pydocstyle)

## Common Patterns

### Error Handling

```python
# ✅ CORRECT - Specific exceptions, clear messages
try:
    token = provider.acquire_token()
except requests.RequestException as e:
    raise TokenAcquisitionError(f"Failed to acquire token: {e}") from e
except ValueError as e:
    logger.error(f"Invalid configuration: {e}")
    raise
```

### Logging

```python
# ✅ CORRECT - Use structured logger
logger.info(
    "Token acquired successfully",
    extra={
        "server_name": server_name,
        "expires_in": token.expires_in,
        "token_type": token.token_type,
    },
)

# ❌ INCORRECT - Avoid f-string interpolation in log messages
logger.info(f"Token acquired for {server_name} expires in {token.expires_in}s")
```

### Configuration

```python
# ✅ CORRECT - Use dataclasses with type hints
from dataclasses import dataclass
from typing import Optional

@dataclass
class OAuthConfig:
    """OAuth provider configuration."""

    client_id: str
    client_secret: str
    token_endpoint: str
    scope: Optional[str] = None
    verify_ssl: bool = True
```

## Resources

- [PEP 8 - Style Guide for Python Code](https://peps.python.org/pep-0008/)
- [PEP 484 - Type Hints](https://peps.python.org/pep-0484/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [Black - The Uncompromising Code Formatter](https://black.readthedocs.io/)
- [mypy - Optional Static Typing for Python](https://mypy.readthedocs.io/)

## Enforcement

**All pull requests must:**
1. Pass all pre-commit hooks
2. Pass all CI checks
3. Maintain or improve code coverage
4. Include tests for new functionality
5. Update documentation as needed

**Code review checklist:**
- [ ] Code follows formatting standards (black, isort)
- [ ] All functions have type hints
- [ ] All public functions have docstrings
- [ ] No magic numbers
- [ ] Complexity is reasonable (< 7 per function)
- [ ] Tests are included and passing
- [ ] No security issues (bandit clean)
- [ ] Documentation is updated
