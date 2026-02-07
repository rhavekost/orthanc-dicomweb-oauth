# Architectural & Technical Improvement Plan

**Project:** Orthanc DICOMweb OAuth Plugin
**Version:** 1.0.0 → 2.0.0
**Target Date:** 8 weeks from start
**Document Version:** 1.0
**Last Updated:** February 6, 2026

---

## Table of Contents

1. [Overview](#overview)
2. [Priority 1: High Impact, Low Effort (Week 1)](#priority-1-high-impact-low-effort-week-1)
3. [Priority 2: High Impact, Medium Effort (Weeks 2-4)](#priority-2-high-impact-medium-effort-weeks-2-4)
4. [Priority 3: Medium Impact, High Effort (Weeks 5-8)](#priority-3-medium-impact-high-effort-weeks-5-8)
5. [Implementation Timeline](#implementation-timeline)
6. [Testing Strategy](#testing-strategy)
7. [Migration Guide](#migration-guide)
8. [Success Criteria](#success-criteria)

---

## Overview

### Current Issues Summary

| Issue | Impact | Priority | Effort |
|-------|--------|----------|--------|
| Global state management | High | P1 | Low |
| No structured logging | High | P1 | Low |
| No version pinning | High | P1 | Low |
| No OAuth provider abstraction | High | P2 | Medium |
| No connection pooling | High | P2 | Medium |
| No circuit breaker | High | P2 | Medium |
| No token cache limits | Medium | P2 | Medium |
| No vulnerability scanning | Medium | P2 | Medium |
| Missing JWT library | High | P1 | Low |
| No async/await | Medium | P3 | High |
| No hot config reload | Medium | P3 | High |

### Overall Goal

**Transform from v1.0 (Score: 68.6/100) to v2.0 (Target: 85/100)**

**Key Improvements:**
- Architecture: 72 → 85 (+13 points)
- Maintainability: 58 → 80 (+22 points)
- Security: 62 → 90 (+28 points)

**Total Effort:** ~15-20 developer-days (3-4 weeks for 1 developer)

---

## Priority 1: High Impact, Low Effort (Week 1)

**Total Effort:** 3-4 days
**Impact:** Immediate code quality and security improvements

### 1.1 Pin Exact Dependency Versions (2 hours)

**Issue:** Using `>=` allows untested versions, potential supply chain attacks
**Impact:** Reproducible builds, security

#### Implementation Steps

**Step 1: Pin production dependencies**

```bash
# Current requirements.txt
requests>=2.31.0  # ❌ Unsafe

# New requirements.txt
requests==2.31.0  # ✅ Pinned
```

**Step 2: Create lockfile**

```bash
# Generate exact dependency tree
pip freeze > requirements.lock

# Contents:
requests==2.31.0
urllib3==2.1.0
certifi==2023.11.17
charset-normalizer==3.3.2
idna==3.6
```

**Step 3: Update development dependencies**

```bash
# requirements-dev.txt
-r requirements.txt
pytest==7.4.3
pytest-cov==4.1.0
pytest-mock==3.12.0
responses==0.24.1
coverage==7.3.4
pre-commit==3.6.0
black==23.12.1
flake8==7.0.0
mypy==1.8.0
bandit==1.7.6
isort==5.13.2
types-requests==2.31.0.20240106
```

**Step 4: Update CI/CD**

```yaml
# .github/workflows/ci.yml
- name: Install dependencies
  run: |
    python -m pip install --upgrade pip==23.3.2
    pip install -r requirements.lock  # ✅ Use lockfile
    pip install -r requirements-dev.txt
```

**Step 5: Add dependency verification**

```bash
# .github/workflows/security.yml
- name: Verify dependencies
  run: |
    pip install pip-audit==2.6.1
    pip-audit -r requirements.lock --desc
```

#### Testing

```bash
# Test with pinned versions
pip install -r requirements.lock
pytest tests/ -v

# Verify all tests pass
```

#### Success Criteria

- ✅ All dependencies pinned to exact versions
- ✅ requirements.lock generated and committed
- ✅ CI/CD uses lockfile
- ✅ All tests pass with pinned versions

---

### 1.2 Add Cryptography Library for JWT Validation (1 hour)

**Issue:** Missing JWT validation capabilities
**Impact:** Security vulnerability (CV-5)

#### Implementation Steps

**Step 1: Add dependencies**

```bash
# requirements.txt
requests==2.31.0
PyJWT==2.8.0          # ✅ Add JWT library
cryptography==42.0.0  # ✅ Add crypto library (required by PyJWT)
```

**Step 2: Regenerate lockfile**

```bash
pip install -r requirements.txt
pip freeze > requirements.lock
```

**Step 3: Update requirements-dev.txt**

```bash
# requirements-dev.txt
...existing...
types-PyJWT==2.8.0  # ✅ Add type stubs
```

#### Testing

```bash
# Verify import works
python -c "import jwt; print(jwt.__version__)"
# Output: 2.8.0
```

#### Success Criteria

- ✅ PyJWT and cryptography installed
- ✅ Type stubs added
- ✅ No dependency conflicts

---

### 1.3 Implement Dependency Injection Pattern (1 day)

**Issue:** Global state makes testing difficult
**Current Code:** `dicomweb_oauth_plugin.py:26-28`

```python
# ❌ BEFORE: Global state
_token_managers: Dict[str, TokenManager] = {}
_server_urls: Dict[str, str] = {}
```

#### Implementation Steps

**Step 1: Create Plugin Context class**

```python
# src/plugin_context.py (NEW FILE)
"""Plugin context for dependency injection."""
from typing import Dict, Optional
from src.token_manager import TokenManager


class PluginContext:
    """
    Central context for plugin state and dependencies.

    Replaces global variables with dependency injection pattern.
    All plugin state is encapsulated in this class.
    """

    def __init__(self):
        self.token_managers: Dict[str, TokenManager] = {}
        self.server_urls: Dict[str, str] = {}
        self.audit_logger: Optional['AuditLogger'] = None  # Will add later
        self.metrics_collector: Optional['MetricsCollector'] = None  # Will add later

    def get_token_manager(self, server_name: str) -> Optional[TokenManager]:
        """Get token manager for a server."""
        return self.token_managers.get(server_name)

    def get_server_url(self, server_name: str) -> Optional[str]:
        """Get URL for a server."""
        return self.server_urls.get(server_name)

    def find_server_for_uri(self, uri: str) -> Optional[str]:
        """Find which configured server a URI belongs to."""
        for server_name, server_url in self.server_urls.items():
            if uri.startswith(server_url):
                return server_name
        return None

    def register_token_manager(self, server_name: str, manager: TokenManager, url: str):
        """Register a token manager for a server."""
        self.token_managers[server_name] = manager
        self.server_urls[server_name] = url
```

**Step 2: Refactor plugin initialization**

```python
# src/dicomweb_oauth_plugin.py (MODIFIED)
from src.plugin_context import PluginContext

# ✅ AFTER: Single global context instance
_plugin_context: Optional[PluginContext] = None


def initialize_plugin(orthanc_module=None, context: Optional[PluginContext] = None):
    """
    Initialize the DICOMweb OAuth plugin.

    Args:
        orthanc_module: Orthanc module (for testing, defaults to global orthanc)
        context: Plugin context (for testing, creates new if None)
    """
    global _plugin_context

    if orthanc_module is None:
        orthanc_module = orthanc

    # Create or use provided context (allows dependency injection in tests)
    if context is None:
        context = PluginContext()

    _plugin_context = context

    logger.info("Initializing DICOMweb OAuth plugin")

    try:
        # Load configuration
        config = orthanc_module.GetConfiguration()
        parser = ConfigParser(config)
        servers = parser.get_servers()

        # Initialize token manager for each configured server
        for server_name, server_config in servers.items():
            logger.info(f"Configuring OAuth for server: {server_name}")

            manager = TokenManager(server_name, server_config)
            context.register_token_manager(
                server_name=server_name,
                manager=manager,
                url=server_config["Url"]
            )

            logger.info(
                f"Server '{server_name}' configured with URL: {server_config['Url']}"
            )

        logger.info(f"DICOMweb OAuth plugin initialized with {len(servers)} server(s)")

    except ConfigError as e:
        logger.error(f"Configuration error: {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to initialize plugin: {e}")
        raise


def get_plugin_context() -> PluginContext:
    """Get the plugin context (for use in callbacks)."""
    if _plugin_context is None:
        raise RuntimeError("Plugin not initialized")
    return _plugin_context
```

**Step 3: Refactor HTTP request handler**

```python
# src/dicomweb_oauth_plugin.py (MODIFIED)
def on_outgoing_http_request(
    uri: str,
    method: str,
    headers: Dict[str, str],
    get_params: Dict[str, str],
    body: bytes,
) -> Optional[Dict]:
    """
    Orthanc HTTP filter callback - injects OAuth2 bearer tokens.
    """
    context = get_plugin_context()

    # Find which server this request is for
    server_name = context.find_server_for_uri(uri)

    if server_name is None:
        # Not a configured OAuth server, let it pass through
        return None

    logger.debug(f"Injecting OAuth token for server '{server_name}'")

    try:
        # Get valid token
        token_manager = context.get_token_manager(server_name)
        if token_manager is None:
            logger.error(f"No token manager for server '{server_name}'")
            return None

        token = token_manager.get_token()

        # Inject Authorization header
        headers["Authorization"] = f"Bearer {token}"

        # Return modified request
        return {
            "headers": headers,
            "method": method,
            "uri": uri,
            "get_params": get_params,
            "body": body,
        }

    except TokenAcquisitionError as e:
        logger.error(f"Failed to acquire token for '{server_name}': {e}")
        return {
            "status": 503,
            "body": json.dumps(
                {
                    "error": "OAuth token acquisition failed",
                    "server": server_name,
                    "details": str(e),
                }
            ),
        }
```

**Step 4: Refactor REST API handlers**

```python
# src/dicomweb_oauth_plugin.py (MODIFIED)
def handle_rest_api_status(output, uri, **request) -> None:
    """GET /dicomweb-oauth/status"""
    context = get_plugin_context()

    status = {
        "plugin": "DICOMweb OAuth",
        "version": __version__,
        "status": "active",
        "configured_servers": len(context.token_managers),
        "servers": list(context.token_managers.keys()),
    }

    output.AnswerBuffer(json.dumps(status, indent=2), "application/json")


def handle_rest_api_servers(output, uri, **request) -> None:
    """GET /dicomweb-oauth/servers"""
    context = get_plugin_context()

    servers = []
    for server_name, token_manager in context.token_managers.items():
        server_info = {
            "name": server_name,
            "url": context.get_server_url(server_name),
            "token_endpoint": token_manager.token_endpoint,
            "has_cached_token": token_manager._cached_token is not None,
            "token_valid": token_manager._is_token_valid()
            if token_manager._cached_token
            else False,
        }
        servers.append(server_info)

    output.AnswerBuffer(json.dumps({"servers": servers}, indent=2), "application/json")
```

#### Testing

**Unit tests can now inject mock context:**

```python
# tests/test_plugin_integration.py (MODIFIED)
import pytest
from src.plugin_context import PluginContext
from src.dicomweb_oauth_plugin import initialize_plugin


def test_plugin_initialization_with_injected_context():
    """Test plugin initialization with dependency injection."""
    # Arrange: Create mock context
    context = PluginContext()

    mock_orthanc = MockOrthanc()
    mock_orthanc.config = {
        "DicomWebOAuth": {
            "Servers": {
                "test-server": {
                    "Url": "https://dicom.example.com/",
                    "TokenEndpoint": "https://login.example.com/token",
                    "ClientId": "client123",
                    "ClientSecret": "secret456",
                }
            }
        }
    }

    # Act: Initialize with injected context
    initialize_plugin(orthanc_module=mock_orthanc, context=context)

    # Assert: Context populated correctly
    assert len(context.token_managers) == 1
    assert "test-server" in context.token_managers
    assert context.get_server_url("test-server") == "https://dicom.example.com/"


def test_find_server_for_uri():
    """Test URI matching against configured servers."""
    context = PluginContext()
    context.server_urls = {
        "azure-dicom": "https://dicom.azure.com/",
        "google-dicom": "https://dicom.google.com/",
    }

    # Test exact match
    assert context.find_server_for_uri("https://dicom.azure.com/studies") == "azure-dicom"

    # Test prefix match
    assert context.find_server_for_uri("https://dicom.google.com/series/123") == "google-dicom"

    # Test no match
    assert context.find_server_for_uri("https://unknown.com/data") is None
```

#### Success Criteria

- ✅ No global dictionaries (except `_plugin_context`)
- ✅ All tests pass with dependency injection
- ✅ Plugin can be instantiated multiple times in tests
- ✅ No breaking changes to external API

---

### 1.4 Implement Structured Logging with JSON Output (1 day)

**Issue:** Scattered logging, difficult to parse
**Impact:** Production troubleshooting

#### Implementation Steps

**Step 1: Create structured logger module**

```python
# src/structured_logger.py (NEW FILE)
"""Structured logging for OAuth plugin."""
import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional


class StructuredLogger:
    """
    Structured logger that outputs JSON-formatted log entries.

    Each log entry includes:
    - timestamp (ISO 8601)
    - level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    - message
    - context fields (server, operation, etc.)
    - correlation_id (for request tracing)
    """

    def __init__(self, name: str = "oauth-plugin"):
        self.logger = logging.getLogger(name)
        self.context: Dict[str, Any] = {}
        self._setup_handler()

    def _setup_handler(self):
        """Setup JSON formatter and handler."""
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter())
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def set_context(self, **kwargs):
        """Set context fields to include in all log entries."""
        self.context.update(kwargs)

    def clear_context(self):
        """Clear all context fields."""
        self.context.clear()

    def _log(self, level: int, message: str, **kwargs):
        """Internal log method with context."""
        extra_fields = {**self.context, **kwargs}
        self.logger.log(level, message, extra={"fields": extra_fields})

    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self._log(logging.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs):
        """Log info message."""
        self._log(logging.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self._log(logging.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs):
        """Log error message."""
        self._log(logging.ERROR, message, **kwargs)

    def critical(self, message: str, **kwargs):
        """Log critical message."""
        self._log(logging.CRITICAL, message, **kwargs)


class JsonFormatter(logging.Formatter):
    """JSON log formatter."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add extra fields if present
        if hasattr(record, "fields"):
            log_entry.update(record.fields)

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)


# Global structured logger instance
structured_logger = StructuredLogger()
```

**Step 2: Integrate into TokenManager**

```python
# src/token_manager.py (MODIFIED)
from src.structured_logger import structured_logger


class TokenManager:
    def __init__(self, server_name: str, config: Dict[str, Any]):
        self.server_name = server_name
        # ... existing init code ...

        # Set context for all logs from this manager
        structured_logger.set_context(server=server_name)

    def get_token(self) -> str:
        """Get a valid OAuth2 access token."""
        with self._lock:
            if self._is_token_valid():
                structured_logger.debug(
                    "Using cached token",
                    operation="get_token",
                    cached=True,
                )
                return self._cached_token

            structured_logger.info(
                "Acquiring new token",
                operation="get_token",
                cached=False,
            )
            return self._acquire_token()

    def _acquire_token(self) -> str:
        """Acquire a new OAuth2 token."""
        structured_logger.info(
            "Starting token acquisition",
            operation="acquire_token",
            endpoint=self.token_endpoint,
        )

        # ... existing code ...

        for attempt in range(max_retries):
            try:
                response = requests.post(...)
                response.raise_for_status()

                token_data = response.json()
                self._cached_token = token_data["access_token"]
                expires_in = token_data.get("expires_in", 3600)
                self._token_expiry = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

                structured_logger.info(
                    "Token acquired successfully",
                    operation="acquire_token",
                    expires_in_seconds=expires_in,
                    attempt=attempt + 1,
                )

                return self._cached_token

            except (requests.Timeout, requests.ConnectionError) as e:
                structured_logger.warning(
                    "Token acquisition retry",
                    operation="acquire_token",
                    attempt=attempt + 1,
                    max_attempts=max_retries,
                    error_type=type(e).__name__,
                    error_message=str(e),
                    retry_delay_seconds=retry_delay,
                )

                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    error_msg = f"Failed after {max_retries} attempts: {e}"
                    structured_logger.error(
                        "Token acquisition failed",
                        operation="acquire_token",
                        error_type=type(e).__name__,
                        error_message=str(e),
                        max_attempts=max_retries,
                    )
                    raise TokenAcquisitionError(error_msg) from e
```

**Step 3: Example JSON log output**

```json
{
  "timestamp": "2026-02-06T21:00:00.123456Z",
  "level": "INFO",
  "message": "Token acquired successfully",
  "logger": "oauth-plugin",
  "module": "token_manager",
  "function": "_acquire_token",
  "line": 142,
  "server": "azure-dicom",
  "operation": "acquire_token",
  "expires_in_seconds": 3600,
  "attempt": 1
}
```

**Step 4: Add configuration for log format**

```json
// docker/orthanc.json
{
  "DicomWebOAuth": {
    "LogFormat": "json",  // Options: "json", "text"
    "LogLevel": "INFO",   // Options: "DEBUG", "INFO", "WARNING", "ERROR"
    "Servers": { ... }
  }
}
```

#### Testing

```python
# tests/test_structured_logging.py (NEW FILE)
import json
from io import StringIO
import logging
from src.structured_logger import StructuredLogger, JsonFormatter


def test_json_formatter():
    """Test JSON log formatter."""
    # Arrange
    logger = StructuredLogger("test")
    output = StringIO()
    handler = logging.StreamHandler(output)
    handler.setFormatter(JsonFormatter())
    logger.logger.addHandler(handler)

    # Act
    logger.info("Test message", server="test-server", operation="test_op")

    # Assert
    log_output = output.getvalue()
    log_entry = json.loads(log_output)

    assert log_entry["level"] == "INFO"
    assert log_entry["message"] == "Test message"
    assert log_entry["server"] == "test-server"
    assert log_entry["operation"] == "test_op"
    assert "timestamp" in log_entry


def test_context_propagation():
    """Test context fields propagate to all logs."""
    logger = StructuredLogger("test")
    output = StringIO()
    handler = logging.StreamHandler(output)
    handler.setFormatter(JsonFormatter())
    logger.logger.addHandler(handler)

    # Set context
    logger.set_context(server="azure-dicom", request_id="12345")

    # Log multiple messages
    logger.info("First message")
    logger.info("Second message")

    # Assert context in both
    lines = output.getvalue().strip().split("\n")
    for line in lines:
        log_entry = json.loads(line)
        assert log_entry["server"] == "azure-dicom"
        assert log_entry["request_id"] == "12345"
```

#### Success Criteria

- ✅ All logs output as JSON
- ✅ Context fields propagate correctly
- ✅ No sensitive data (tokens, secrets) in logs
- ✅ Logs parseable by log aggregation tools (ELK, Splunk)

---

## Priority 2: High Impact, Medium Effort (Weeks 2-4)

**Total Effort:** 10-12 days
**Impact:** Scalability, extensibility, resilience

### 2.1 Implement Provider Factory Pattern (3 days)

**Issue:** No abstraction for OAuth providers
**Impact:** Hard to add new providers

#### Implementation Steps

**Step 1: Create OAuth provider interface**

```python
# src/oauth_providers/base.py (NEW FILE)
"""Base OAuth provider interface."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class OAuthToken:
    """OAuth token response."""
    access_token: str
    expires_in: int
    token_type: str = "Bearer"
    refresh_token: Optional[str] = None
    scope: Optional[str] = None


@dataclass
class OAuthConfig:
    """OAuth provider configuration."""
    token_endpoint: str
    client_id: str
    client_secret: str
    scope: str = ""
    verify_ssl: bool = True


class OAuthProvider(ABC):
    """
    Abstract base class for OAuth providers.

    Implementations must provide token acquisition logic
    specific to each OAuth provider (Azure, Google, Keycloak, etc.).
    """

    def __init__(self, config: OAuthConfig):
        self.config = config

    @abstractmethod
    def acquire_token(self) -> OAuthToken:
        """
        Acquire an OAuth token from the provider.

        Returns:
            OAuthToken with access token and expiry

        Raises:
            TokenAcquisitionError: If acquisition fails
        """
        pass

    @abstractmethod
    def validate_token(self, token: str) -> bool:
        """
        Validate token signature (if applicable).

        Args:
            token: JWT token to validate

        Returns:
            True if valid, False otherwise
        """
        pass

    @abstractmethod
    def refresh_token(self, refresh_token: str) -> OAuthToken:
        """
        Refresh an access token using a refresh token.

        Args:
            refresh_token: Refresh token

        Returns:
            New OAuthToken

        Raises:
            TokenAcquisitionError: If refresh fails
        """
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name (e.g., 'azure', 'google')."""
        pass
```

**Step 2: Implement generic OAuth2 provider**

```python
# src/oauth_providers/generic.py (NEW FILE)
"""Generic OAuth2 client credentials provider."""
import requests
from typing import Dict, Any
from src.oauth_providers.base import OAuthProvider, OAuthToken, OAuthConfig
from src.token_manager import TokenAcquisitionError


class GenericOAuth2Provider(OAuthProvider):
    """
    Generic OAuth2 client credentials flow provider.

    Works with any OAuth2-compliant provider that supports
    the client credentials grant type.
    """

    @property
    def provider_name(self) -> str:
        return "generic-oauth2"

    def acquire_token(self) -> OAuthToken:
        """Acquire token using client credentials flow."""
        data = {
            "grant_type": "client_credentials",
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
        }

        if self.config.scope:
            data["scope"] = self.config.scope

        try:
            response = requests.post(
                self.config.token_endpoint,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=30,
                verify=self.config.verify_ssl,
            )
            response.raise_for_status()

            token_data = response.json()
            return OAuthToken(
                access_token=token_data["access_token"],
                expires_in=token_data.get("expires_in", 3600),
                token_type=token_data.get("token_type", "Bearer"),
                refresh_token=token_data.get("refresh_token"),
                scope=token_data.get("scope"),
            )

        except requests.RequestException as e:
            raise TokenAcquisitionError(f"Failed to acquire token: {e}") from e
        except (KeyError, ValueError) as e:
            raise TokenAcquisitionError(f"Invalid token response: {e}") from e

    def validate_token(self, token: str) -> bool:
        """Generic provider doesn't validate tokens."""
        return True  # Override in provider-specific implementations

    def refresh_token(self, refresh_token: str) -> OAuthToken:
        """Refresh access token."""
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
        }

        try:
            response = requests.post(
                self.config.token_endpoint,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=30,
                verify=self.config.verify_ssl,
            )
            response.raise_for_status()

            token_data = response.json()
            return OAuthToken(
                access_token=token_data["access_token"],
                expires_in=token_data.get("expires_in", 3600),
                token_type=token_data.get("token_type", "Bearer"),
                refresh_token=token_data.get("refresh_token", refresh_token),
                scope=token_data.get("scope"),
            )

        except requests.RequestException as e:
            raise TokenAcquisitionError(f"Failed to refresh token: {e}") from e
```

**Step 3: Implement Azure-specific provider**

```python
# src/oauth_providers/azure.py (NEW FILE)
"""Azure Active Directory (Entra ID) OAuth provider."""
import jwt
from jwt import PyJWKClient
from src.oauth_providers.generic import GenericOAuth2Provider
from src.oauth_providers.base import OAuthConfig


class AzureOAuthProvider(GenericOAuth2Provider):
    """
    Azure AD (Entra ID) OAuth provider.

    Adds Azure-specific features:
    - JWT signature validation using Azure's JWKS endpoint
    - Azure-specific token endpoints
    - Tenant-aware configuration
    """

    def __init__(self, config: OAuthConfig, tenant_id: str):
        super().__init__(config)
        self.tenant_id = tenant_id
        self.jwks_uri = f"https://login.microsoftonline.com/{tenant_id}/discovery/v2.0/keys"
        self.issuer = f"https://login.microsoftonline.com/{tenant_id}/v2.0"

    @property
    def provider_name(self) -> str:
        return "azure-ad"

    def validate_token(self, token: str) -> bool:
        """Validate JWT signature using Azure's JWKS."""
        try:
            jwks_client = PyJWKClient(self.jwks_uri)
            signing_key = jwks_client.get_signing_key_from_jwt(token)

            jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=self.config.client_id,
                issuer=self.issuer,
            )
            return True

        except jwt.InvalidTokenError:
            return False
```

**Step 4: Create provider factory**

```python
# src/oauth_providers/factory.py (NEW FILE)
"""OAuth provider factory."""
from typing import Dict, Any, Type
from src.oauth_providers.base import OAuthProvider, OAuthConfig
from src.oauth_providers.generic import GenericOAuth2Provider
from src.oauth_providers.azure import AzureOAuthProvider


class OAuthProviderFactory:
    """
    Factory for creating OAuth provider instances.

    Supports automatic provider detection or explicit specification.
    """

    # Registry of provider types
    _providers: Dict[str, Type[OAuthProvider]] = {
        "generic": GenericOAuth2Provider,
        "azure": AzureOAuthProvider,
        # Add more providers here as implemented:
        # "google": GoogleOAuthProvider,
        # "keycloak": KeycloakOAuthProvider,
    }

    @classmethod
    def create(cls, provider_type: str, config: Dict[str, Any]) -> OAuthProvider:
        """
        Create an OAuth provider instance.

        Args:
            provider_type: Provider type (e.g., 'azure', 'google', 'generic')
            config: Provider configuration dict

        Returns:
            OAuthProvider instance

        Raises:
            ValueError: If provider type is unknown
        """
        if provider_type not in cls._providers:
            raise ValueError(
                f"Unknown provider type: {provider_type}. "
                f"Supported: {list(cls._providers.keys())}"
            )

        # Convert dict config to OAuthConfig
        oauth_config = OAuthConfig(
            token_endpoint=config["TokenEndpoint"],
            client_id=config["ClientId"],
            client_secret=config["ClientSecret"],
            scope=config.get("Scope", ""),
            verify_ssl=config.get("VerifySSL", True),
        )

        # Provider-specific initialization
        provider_class = cls._providers[provider_type]

        if provider_type == "azure":
            tenant_id = config.get("TenantId", "common")
            return provider_class(oauth_config, tenant_id)
        else:
            return provider_class(oauth_config)

    @classmethod
    def register_provider(cls, provider_type: str, provider_class: Type[OAuthProvider]):
        """Register a custom provider type."""
        cls._providers[provider_type] = provider_class

    @classmethod
    def auto_detect(cls, config: Dict[str, Any]) -> str:
        """
        Auto-detect provider type from configuration.

        Args:
            config: Provider configuration dict

        Returns:
            Detected provider type
        """
        token_endpoint = config.get("TokenEndpoint", "")

        # Azure detection
        if "login.microsoftonline.com" in token_endpoint:
            return "azure"

        # Google detection
        if "oauth2.googleapis.com" in token_endpoint:
            return "google"

        # Keycloak detection
        if "/auth/realms/" in token_endpoint:
            return "keycloak"

        # Default to generic
        return "generic"
```

**Step 5: Refactor TokenManager to use provider**

```python
# src/token_manager.py (MODIFIED)
from src.oauth_providers.factory import OAuthProviderFactory
from src.oauth_providers.base import OAuthProvider


class TokenManager:
    """OAuth2 token manager using provider abstraction."""

    def __init__(self, server_name: str, config: Dict[str, Any]):
        self.server_name = server_name
        self.config = config
        self._validate_config()

        # Token cache
        self._cached_token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None
        self._lock = threading.Lock()

        # Configuration
        self.refresh_buffer_seconds = config.get("TokenRefreshBufferSeconds", 300)

        # Create OAuth provider
        provider_type = config.get("ProviderType", "auto")
        if provider_type == "auto":
            provider_type = OAuthProviderFactory.auto_detect(config)

        self.provider: OAuthProvider = OAuthProviderFactory.create(
            provider_type=provider_type,
            config=config
        )

        structured_logger.info(
            "Token manager initialized",
            server=server_name,
            provider=self.provider.provider_name,
        )

    def _acquire_token(self) -> str:
        """Acquire token using provider."""
        structured_logger.info(
            "Acquiring token from provider",
            server=self.server_name,
            provider=self.provider.provider_name,
        )

        try:
            oauth_token = self.provider.acquire_token()

            self._cached_token = oauth_token.access_token
            self._token_expiry = datetime.now(timezone.utc) + timedelta(
                seconds=oauth_token.expires_in
            )

            # Validate token if provider supports it
            if not self.provider.validate_token(oauth_token.access_token):
                raise TokenAcquisitionError("Token validation failed")

            structured_logger.info(
                "Token acquired and validated",
                server=self.server_name,
                expires_in=oauth_token.expires_in,
            )

            return self._cached_token

        except Exception as e:
            structured_logger.error(
                "Token acquisition failed",
                server=self.server_name,
                error=str(e),
            )
            raise
```

**Step 6: Update configuration**

```json
// docker/orthanc.json
{
  "DicomWebOAuth": {
    "Servers": {
      "azure-dicom": {
        "Url": "https://dicom.azure.com/",
        "ProviderType": "azure",  // ✅ Explicit provider type
        "TokenEndpoint": "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token",
        "TenantId": "your-tenant-id",
        "ClientId": "${AZURE_CLIENT_ID}",
        "ClientSecret": "${AZURE_CLIENT_SECRET}",
        "Scope": "https://dicom.healthcareapis.azure.com/.default"
      },
      "generic-dicom": {
        "Url": "https://dicom.example.com/",
        "ProviderType": "auto",  // ✅ Auto-detect from endpoint
        "TokenEndpoint": "https://auth.example.com/oauth2/token",
        "ClientId": "${OAUTH_CLIENT_ID}",
        "ClientSecret": "${OAUTH_CLIENT_SECRET}"
      }
    }
  }
}
```

#### Testing

```python
# tests/test_oauth_providers.py (NEW FILE)
import pytest
from src.oauth_providers.factory import OAuthProviderFactory
from src.oauth_providers.azure import AzureOAuthProvider
from src.oauth_providers.generic import GenericOAuth2Provider


def test_provider_factory_azure():
    """Test creating Azure provider."""
    config = {
        "TokenEndpoint": "https://login.microsoftonline.com/tenant/oauth2/v2.0/token",
        "TenantId": "test-tenant",
        "ClientId": "client123",
        "ClientSecret": "secret456",
        "Scope": "https://dicom.healthcareapis.azure.com/.default",
    }

    provider = OAuthProviderFactory.create("azure", config)

    assert isinstance(provider, AzureOAuthProvider)
    assert provider.provider_name == "azure-ad"
    assert provider.tenant_id == "test-tenant"


def test_provider_factory_generic():
    """Test creating generic provider."""
    config = {
        "TokenEndpoint": "https://auth.example.com/token",
        "ClientId": "client123",
        "ClientSecret": "secret456",
    }

    provider = OAuthProviderFactory.create("generic", config)

    assert isinstance(provider, GenericOAuth2Provider)
    assert provider.provider_name == "generic-oauth2"


def test_auto_detect_azure():
    """Test auto-detecting Azure provider."""
    config = {
        "TokenEndpoint": "https://login.microsoftonline.com/tenant/oauth2/v2.0/token",
    }

    provider_type = OAuthProviderFactory.auto_detect(config)
    assert provider_type == "azure"


def test_auto_detect_generic():
    """Test auto-detecting generic provider."""
    config = {
        "TokenEndpoint": "https://auth.example.com/token",
    }

    provider_type = OAuthProviderFactory.auto_detect(config)
    assert provider_type == "generic"
```

#### Success Criteria

- ✅ Provider interface defined
- ✅ At least 2 providers implemented (generic, Azure)
- ✅ Factory pattern working
- ✅ Auto-detection working
- ✅ All existing tests pass
- ✅ Backward compatible (auto-detect for old configs)

---

### 2.2 Add Connection Pooling for OAuth Requests (1 day)

**Issue:** New connection for each token request
**Impact:** Latency, resource usage

#### Implementation Steps

**Step 1: Create HTTP client with pooling**

```python
# src/http_client.py (NEW FILE)
"""HTTP client with connection pooling for OAuth requests."""
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class PooledHTTPClient:
    """
    HTTP client with connection pooling and retry logic.

    Reuses TCP connections to OAuth providers for better performance.
    """

    def __init__(
        self,
        pool_connections: int = 10,
        pool_maxsize: int = 20,
        max_retries: int = 3,
    ):
        """
        Initialize pooled HTTP client.

        Args:
            pool_connections: Number of connection pools to cache
            pool_maxsize: Maximum number of connections per pool
            max_retries: Maximum number of retries
        """
        self.session = requests.Session()

        # Configure retry strategy
        retry_strategy = Retry(
            total=max_retries,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST"],
            backoff_factor=1,  # 1s, 2s, 4s
        )

        # Configure adapter with pooling
        adapter = HTTPAdapter(
            pool_connections=pool_connections,
            pool_maxsize=pool_maxsize,
            max_retries=retry_strategy,
        )

        # Mount adapter for both http and https
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def post(self, url: str, **kwargs) -> requests.Response:
        """Make POST request using pooled session."""
        return self.session.post(url, **kwargs)

    def close(self):
        """Close session and release connections."""
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


# Global HTTP client instance
_http_client: Optional[PooledHTTPClient] = None


def get_http_client() -> PooledHTTPClient:
    """Get global HTTP client instance."""
    global _http_client
    if _http_client is None:
        _http_client = PooledHTTPClient()
    return _http_client
```

**Step 2: Use pooled client in providers**

```python
# src/oauth_providers/generic.py (MODIFIED)
from src.http_client import get_http_client


class GenericOAuth2Provider(OAuthProvider):
    def acquire_token(self) -> OAuthToken:
        """Acquire token using pooled HTTP client."""
        data = {
            "grant_type": "client_credentials",
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
        }

        if self.config.scope:
            data["scope"] = self.config.scope

        try:
            # Use pooled HTTP client
            http_client = get_http_client()
            response = http_client.post(
                self.config.token_endpoint,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=30,
                verify=self.config.verify_ssl,
            )
            response.raise_for_status()

            # ... rest of implementation
```

#### Testing

```python
# tests/test_http_client.py (NEW FILE)
import pytest
import responses
from src.http_client import PooledHTTPClient, get_http_client


@responses.activate
def test_connection_reuse():
    """Test that connections are reused."""
    responses.add(
        responses.POST,
        "https://auth.example.com/token",
        json={"access_token": "token123"},
        status=200,
    )

    client = PooledHTTPClient()

    # Make multiple requests
    for _ in range(5):
        response = client.post("https://auth.example.com/token", data={})
        assert response.status_code == 200

    # Assert: Only 1 connection established (reused 5 times)
    # (This would require mocking socket connections to verify)


@responses.activate
def test_automatic_retry():
    """Test automatic retry on 503 errors."""
    # First request returns 503
    responses.add(
        responses.POST,
        "https://auth.example.com/token",
        status=503,
    )
    # Second request returns 200
    responses.add(
        responses.POST,
        "https://auth.example.com/token",
        json={"access_token": "token123"},
        status=200,
    )

    client = PooledHTTPClient(max_retries=1)
    response = client.post("https://auth.example.com/token", data={})

    # Should succeed after retry
    assert response.status_code == 200
```

#### Success Criteria

- ✅ HTTP connections reused
- ✅ Automatic retry on transient errors
- ✅ Performance improvement (measure latency)
- ✅ No breaking changes

---

### 2.3 Implement Token Cache Size Limits (1 day)

**Issue:** Unbounded token cache can grow indefinitely
**Impact:** Memory leak risk

#### Implementation Steps

**Step 1: Create LRU cache for token managers**

```python
# src/token_cache.py (NEW FILE)
"""LRU cache for token managers."""
from collections import OrderedDict
from threading import Lock
from typing import Optional
from src.token_manager import TokenManager


class TokenManagerCache:
    """
    LRU cache for TokenManager instances.

    Limits memory usage by evicting least recently used managers.
    Thread-safe for concurrent access.
    """

    def __init__(self, maxsize: int = 100):
        """
        Initialize cache.

        Args:
            maxsize: Maximum number of token managers to cache
        """
        self.maxsize = maxsize
        self.cache: OrderedDict[str, TokenManager] = OrderedDict()
        self.lock = Lock()

    def get(self, server_name: str) -> Optional[TokenManager]:
        """Get token manager from cache."""
        with self.lock:
            if server_name in self.cache:
                # Move to end (most recently used)
                self.cache.move_to_end(server_name)
                return self.cache[server_name]
            return None

    def put(self, server_name: str, manager: TokenManager):
        """Put token manager in cache."""
        with self.lock:
            if server_name in self.cache:
                # Update existing
                self.cache.move_to_end(server_name)
                self.cache[server_name] = manager
            else:
                # Add new
                self.cache[server_name] = manager
                self.cache.move_to_end(server_name)

                # Evict if over limit
                if len(self.cache) > self.maxsize:
                    evicted_name, evicted_manager = self.cache.popitem(last=False)
                    structured_logger.info(
                        "Token manager evicted from cache",
                        server=evicted_name,
                        cache_size=len(self.cache),
                    )

    def remove(self, server_name: str):
        """Remove token manager from cache."""
        with self.lock:
            if server_name in self.cache:
                del self.cache[server_name]

    def clear(self):
        """Clear all cached managers."""
        with self.lock:
            self.cache.clear()

    def size(self) -> int:
        """Get current cache size."""
        with self.lock:
            return len(self.cache)
```

**Step 2: Use cache in PluginContext**

```python
# src/plugin_context.py (MODIFIED)
from src.token_cache import TokenManagerCache


class PluginContext:
    def __init__(self, max_cached_managers: int = 100):
        self.token_manager_cache = TokenManagerCache(maxsize=max_cached_managers)
        self.server_urls: Dict[str, str] = {}
        # ... other fields

    def get_token_manager(self, server_name: str) -> Optional[TokenManager]:
        """Get token manager from cache."""
        return self.token_manager_cache.get(server_name)

    def register_token_manager(self, server_name: str, manager: TokenManager, url: str):
        """Register token manager with cache."""
        self.token_manager_cache.put(server_name, manager)
        self.server_urls[server_name] = url
```

**Step 3: Add configuration**

```json
// docker/orthanc.json
{
  "DicomWebOAuth": {
    "MaxCachedServers": 100,  // ✅ Limit token manager cache
    "Servers": { ... }
  }
}
```

#### Testing

```python
# tests/test_token_cache.py (NEW FILE)
from src.token_cache import TokenManagerCache
from src.token_manager import TokenManager


def test_lru_eviction():
    """Test LRU eviction when cache is full."""
    cache = TokenManagerCache(maxsize=3)

    # Add 3 managers
    for i in range(3):
        manager = TokenManager(f"server-{i}", {...})
        cache.put(f"server-{i}", manager)

    assert cache.size() == 3

    # Add 4th manager (should evict server-0)
    manager = TokenManager("server-3", {...})
    cache.put("server-3", manager)

    assert cache.size() == 3
    assert cache.get("server-0") is None  # Evicted
    assert cache.get("server-1") is not None
    assert cache.get("server-2") is not None
    assert cache.get("server-3") is not None


def test_access_updates_lru():
    """Test that accessing an item moves it to end of LRU."""
    cache = TokenManagerCache(maxsize=2)

    manager1 = TokenManager("server-1", {...})
    manager2 = TokenManager("server-2", {...})

    cache.put("server-1", manager1)
    cache.put("server-2", manager2)

    # Access server-1 (moves to end)
    cache.get("server-1")

    # Add server-3 (should evict server-2, not server-1)
    manager3 = TokenManager("server-3", {...})
    cache.put("server-3", manager3)

    assert cache.get("server-1") is not None  # Still cached
    assert cache.get("server-2") is None      # Evicted
    assert cache.get("server-3") is not None
```

#### Success Criteria

- ✅ Cache size limited
- ✅ LRU eviction working
- ✅ Thread-safe
- ✅ No memory leaks

---

### 2.4 Implement Circuit Breaker Pattern (2 days)

**Issue:** No circuit breaker for failing OAuth endpoints
**Impact:** Cascading failures

#### Implementation Steps

**Step 1: Add pybreaker dependency**

```bash
# requirements.txt
requests==2.31.0
PyJWT==2.8.0
cryptography==42.0.0
pybreaker==1.0.2  # ✅ Add circuit breaker library
```

**Step 2: Create circuit breaker wrapper**

```python
# src/circuit_breaker.py (NEW FILE)
"""Circuit breaker for OAuth token acquisition."""
from pybreaker import CircuitBreaker, CircuitBreakerError
from typing import Callable, TypeVar, Any
from src.structured_logger import structured_logger


T = TypeVar('T')


class OAuthCircuitBreaker:
    """
    Circuit breaker for OAuth operations.

    Prevents cascading failures by failing fast when OAuth provider
    is experiencing issues.

    States:
    - Closed: Normal operation
    - Open: Failures detected, fast-failing all requests
    - Half-Open: Testing if service recovered
    """

    def __init__(
        self,
        fail_max: int = 5,           # Open after 5 failures
        timeout_duration: int = 60,   # Stay open for 60 seconds
        name: str = "oauth",
    ):
        """
        Initialize circuit breaker.

        Args:
            fail_max: Number of failures before opening circuit
            timeout_duration: Seconds to wait before trying again
            name: Circuit breaker name (for logging)
        """
        self.breaker = CircuitBreaker(
            fail_max=fail_max,
            timeout_duration=timeout_duration,
            name=name,
        )

        # Register listeners for state changes
        self.breaker.add_listener(self._on_state_change)

    def _on_state_change(self, breaker, old_state, new_state):
        """Log circuit breaker state changes."""
        structured_logger.warning(
            "Circuit breaker state changed",
            breaker=breaker.name,
            old_state=old_state.name,
            new_state=new_state.name,
            failure_count=breaker.fail_counter,
        )

    def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """
        Call function with circuit breaker protection.

        Args:
            func: Function to call
            *args, **kwargs: Arguments to pass to function

        Returns:
            Function result

        Raises:
            CircuitBreakerError: If circuit is open
        """
        try:
            return self.breaker.call(func, *args, **kwargs)
        except CircuitBreakerError:
            structured_logger.error(
                "Circuit breaker open, failing fast",
                breaker=self.breaker.name,
                state=self.breaker.current_state.name,
            )
            raise

    @property
    def state(self) -> str:
        """Get current circuit breaker state."""
        return self.breaker.current_state.name

    def reset(self):
        """Manually reset circuit breaker."""
        self.breaker.call_succeeded()
        structured_logger.info(
            "Circuit breaker manually reset",
            breaker=self.breaker.name,
        )
```

**Step 3: Integrate into OAuth providers**

```python
# src/oauth_providers/generic.py (MODIFIED)
from src.circuit_breaker import OAuthCircuitBreaker


class GenericOAuth2Provider(OAuthProvider):
    def __init__(self, config: OAuthConfig):
        super().__init__(config)

        # Create circuit breaker for this provider
        self.circuit_breaker = OAuthCircuitBreaker(
            fail_max=5,
            timeout_duration=60,
            name=f"oauth-{self.provider_name}",
        )

    def acquire_token(self) -> OAuthToken:
        """Acquire token with circuit breaker protection."""
        try:
            return self.circuit_breaker.call(self._do_acquire_token)
        except CircuitBreakerError:
            raise TokenAcquisitionError(
                f"OAuth provider unavailable (circuit breaker open)"
            )

    def _do_acquire_token(self) -> OAuthToken:
        """Internal token acquisition logic."""
        data = {
            "grant_type": "client_credentials",
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
        }

        if self.config.scope:
            data["scope"] = self.config.scope

        http_client = get_http_client()
        response = http_client.post(
            self.config.token_endpoint,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=30,
            verify=self.config.verify_ssl,
        )
        response.raise_for_status()

        token_data = response.json()
        return OAuthToken(
            access_token=token_data["access_token"],
            expires_in=token_data.get("expires_in", 3600),
        )
```

**Step 4: Add circuit breaker status endpoint**

```python
# src/dicomweb_oauth_plugin.py (ADD NEW ENDPOINT)
def handle_rest_api_circuit_breakers(output, uri, **request) -> None:
    """GET /dicomweb-oauth/circuit-breakers"""
    context = get_plugin_context()

    breakers = []
    for server_name, token_manager in context.token_managers.items():
        breaker_info = {
            "server": server_name,
            "state": token_manager.provider.circuit_breaker.state,
            "failure_count": token_manager.provider.circuit_breaker.breaker.fail_counter,
        }
        breakers.append(breaker_info)

    output.AnswerBuffer(
        json.dumps({"circuit_breakers": breakers}, indent=2),
        "application/json"
    )


# Register endpoint
orthanc.RegisterRestCallback(
    "/dicomweb-oauth/circuit-breakers",
    handle_rest_api_circuit_breakers
)
```

#### Testing

```python
# tests/test_circuit_breaker.py (NEW FILE)
import pytest
from pybreaker import CircuitBreakerError
from src.circuit_breaker import OAuthCircuitBreaker


def test_circuit_breaker_opens_after_failures():
    """Test circuit opens after consecutive failures."""
    breaker = OAuthCircuitBreaker(fail_max=3, timeout_duration=1)

    def failing_function():
        raise Exception("Simulated failure")

    # First 3 calls should raise original exception
    for _ in range(3):
        with pytest.raises(Exception, match="Simulated failure"):
            breaker.call(failing_function)

    # Circuit should now be open
    assert breaker.state == "open"

    # Next call should fail fast
    with pytest.raises(CircuitBreakerError):
        breaker.call(failing_function)


def test_circuit_breaker_half_open_after_timeout():
    """Test circuit transitions to half-open after timeout."""
    breaker = OAuthCircuitBreaker(fail_max=2, timeout_duration=1)

    def failing_function():
        raise Exception("Simulated failure")

    # Trigger circuit open
    for _ in range(2):
        with pytest.raises(Exception):
            breaker.call(failing_function)

    assert breaker.state == "open"

    # Wait for timeout
    import time
    time.sleep(1.1)

    # Should now be half-open (testing recovery)
    # Next failure will re-open circuit
    with pytest.raises(Exception):
        breaker.call(failing_function)


def test_circuit_breaker_closes_on_success():
    """Test circuit closes when call succeeds."""
    breaker = OAuthCircuitBreaker(fail_max=2, timeout_duration=1)

    call_count = [0]

    def flaky_function():
        call_count[0] += 1
        if call_count[0] <= 2:
            raise Exception("Failure")
        return "Success"

    # Trigger circuit open
    for _ in range(2):
        with pytest.raises(Exception):
            breaker.call(flaky_function)

    assert breaker.state == "open"

    # Wait for half-open
    import time
    time.sleep(1.1)

    # Success should close circuit
    result = breaker.call(flaky_function)
    assert result == "Success"
    assert breaker.state == "closed"
```

#### Success Criteria

- ✅ Circuit breaker opens after failures
- ✅ Circuit breaker prevents cascading failures
- ✅ Circuit breaker recovers automatically
- ✅ Status visible via REST API

---

### 2.5 Add Dependency Vulnerability Scanning (0.5 days)

**Issue:** No automated vulnerability scanning
**Impact:** Security risk

#### Implementation Steps

**Step 1: Add safety check to CI**

```yaml
# .github/workflows/security.yml (MODIFIED)
jobs:
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
        run: pip install safety==3.0.1

      - name: Run Safety check on production dependencies
        run: |
          safety check --file requirements.lock \
            --json \
            --output safety-report.json \
            --exit-code 1  # Fail on vulnerabilities

      - name: Run Safety check on dev dependencies
        run: |
          safety check --file requirements-dev.txt \
            --json \
            --output safety-dev-report.json \
            --continue-on-error  # Don't fail on dev vulnerabilities

      - name: Upload Safety reports
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: safety-reports
          path: |
            safety-report.json
            safety-dev-report.json
```

**Step 2: Add pip-audit for more comprehensive scanning**

```yaml
# .github/workflows/security.yml (ADD)
  pip-audit:
    name: Pip Audit Vulnerability Scan
    runs-on: ubuntu-latest

    steps:
      - name: Check out code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install pip-audit
        run: pip install pip-audit==2.6.1

      - name: Run pip-audit
        run: |
          pip-audit \
            --requirement requirements.lock \
            --desc \
            --format json \
            --output pip-audit-report.json

      - name: Upload pip-audit report
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: pip-audit-report
          path: pip-audit-report.json
```

**Step 3: Add pre-commit hook**

```yaml
# .pre-commit-config.yaml (ADD)
repos:
  # ... existing hooks ...

  - repo: https://github.com/Lucas-C/pre-commit-hooks-safety
    rev: v1.3.2
    hooks:
      - id: python-safety-dependencies-check
        files: requirements.*\.txt$
```

**Step 4: Add local vulnerability check script**

```bash
#!/bin/bash
# scripts/check-vulnerabilities.sh (NEW FILE)

set -e

echo "=== Checking for dependency vulnerabilities ==="

# Install tools if needed
pip install -q safety pip-audit

# Check production dependencies
echo "Checking production dependencies (requirements.lock)..."
safety check --file requirements.lock --json --output safety-prod.json

# Check development dependencies
echo "Checking development dependencies (requirements-dev.txt)..."
safety check --file requirements-dev.txt --json --output safety-dev.json

# Run pip-audit
echo "Running pip-audit..."
pip-audit --requirement requirements.lock --desc

echo "✅ No vulnerabilities found!"
```

**Step 5: Document vulnerability response process**

```markdown
# docs/VULNERABILITY-RESPONSE.md (NEW FILE)

# Dependency Vulnerability Response Process

## Automated Scanning

Vulnerabilities are automatically scanned:
- **On every commit** (via pre-commit hooks)
- **On every PR** (via CI/CD)
- **Weekly** (via scheduled GitHub Actions)

## Severity Levels

| Severity | SLA | Action |
|----------|-----|--------|
| **Critical** (CVSS 9.0-10.0) | 24 hours | Immediate patch or mitigation |
| **High** (CVSS 7.0-8.9) | 7 days | Patch in next sprint |
| **Medium** (CVSS 4.0-6.9) | 30 days | Patch when convenient |
| **Low** (CVSS 0.1-3.9) | 90 days | Document and monitor |

## Response Steps

### 1. Alert Received
- Safety/pip-audit detects vulnerability
- GitHub Security Advisory created
- Team notified via Slack/email

### 2. Assessment (2 hours)
- Review CVE details
- Determine exploitability in our context
- Check if vulnerable code path is reachable
- Assign severity level

### 3. Mitigation (per SLA)
- **Immediate**: Update dependency to patched version
- **If no patch available**:
  - Find alternative dependency
  - Implement workaround
  - Document risk and monitoring
- Update `requirements.lock`
- Run full test suite

### 4. Verification
- Rescan with safety/pip-audit
- Verify vulnerability resolved
- Deploy to staging
- Monitor for issues

### 5. Documentation
- Update CHANGELOG.md
- Update SECURITY.md if needed
- Create postmortem if critical
```

#### Success Criteria

- ✅ Automated vulnerability scanning in CI
- ✅ Pre-commit hook prevents committing vulnerable deps
- ✅ Local script for checking vulnerabilities
- ✅ Response process documented

---

## Priority 3: Medium Impact, High Effort (Weeks 5-8)

**Total Effort:** 12-15 days
**Impact:** Performance, operability

### 3.1 Refactor to Async/Await Pattern (7-10 days)

**Issue:** Synchronous I/O blocks threads
**Impact:** Scalability for high-concurrency scenarios

**Note:** This is a significant refactoring. Only implement if you have high-concurrency requirements (100+ requests/sec).

#### Implementation Steps

**Step 1: Add async dependencies**

```bash
# requirements.txt
requests==2.31.0
PyJWT==2.8.0
cryptography==42.0.0
pybreaker==1.0.2
httpx==0.26.0     # ✅ Async HTTP client
anyio==4.2.0      # ✅ Async compatibility layer
```

**Step 2: Create async OAuth provider interface**

```python
# src/oauth_providers/async_base.py (NEW FILE)
"""Async OAuth provider interface."""
from abc import ABC, abstractmethod
from src.oauth_providers.base import OAuthToken, OAuthConfig


class AsyncOAuthProvider(ABC):
    """Async OAuth provider interface."""

    def __init__(self, config: OAuthConfig):
        self.config = config

    @abstractmethod
    async def acquire_token(self) -> OAuthToken:
        """Acquire token asynchronously."""
        pass

    @abstractmethod
    async def validate_token(self, token: str) -> bool:
        """Validate token asynchronously."""
        pass

    @abstractmethod
    async def refresh_token(self, refresh_token: str) -> OAuthToken:
        """Refresh token asynchronously."""
        pass
```

**Step 3: Implement async generic provider**

```python
# src/oauth_providers/async_generic.py (NEW FILE)
"""Async generic OAuth2 provider."""
import httpx
from src.oauth_providers.async_base import AsyncOAuthProvider
from src.oauth_providers.base import OAuthToken
from src.token_manager import TokenAcquisitionError


class AsyncGenericOAuth2Provider(AsyncOAuthProvider):
    """Async OAuth2 client credentials provider."""

    @property
    def provider_name(self) -> str:
        return "async-generic-oauth2"

    async def acquire_token(self) -> OAuthToken:
        """Acquire token asynchronously."""
        data = {
            "grant_type": "client_credentials",
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
        }

        if self.config.scope:
            data["scope"] = self.config.scope

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.config.token_endpoint,
                    data=data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    timeout=30.0,
                )
                response.raise_for_status()

                token_data = response.json()
                return OAuthToken(
                    access_token=token_data["access_token"],
                    expires_in=token_data.get("expires_in", 3600),
                )

            except httpx.HTTPError as e:
                raise TokenAcquisitionError(f"Failed to acquire token: {e}") from e

    async def validate_token(self, token: str) -> bool:
        """Validate token (sync for generic provider)."""
        return True

    async def refresh_token(self, refresh_token: str) -> OAuthToken:
        """Refresh token asynchronously."""
        # Similar to acquire_token but with refresh_token grant
        pass
```

**Step 4: Create async token manager**

```python
# src/async_token_manager.py (NEW FILE)
"""Async token manager."""
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Optional
from src.oauth_providers.async_base import AsyncOAuthProvider


class AsyncTokenManager:
    """
    Async OAuth2 token manager.

    Manages token lifecycle asynchronously for high-performance scenarios.
    """

    def __init__(self, server_name: str, provider: AsyncOAuthProvider):
        self.server_name = server_name
        self.provider = provider
        self._cached_token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None
        self._lock = asyncio.Lock()
        self.refresh_buffer_seconds = 300

    async def get_token(self) -> str:
        """Get valid token asynchronously."""
        async with self._lock:
            if self._is_token_valid():
                return self._cached_token

            return await self._acquire_token()

    def _is_token_valid(self) -> bool:
        """Check if cached token is valid."""
        if self._cached_token is None or self._token_expiry is None:
            return False

        now = datetime.now(timezone.utc)
        buffer = timedelta(seconds=self.refresh_buffer_seconds)
        return now + buffer < self._token_expiry

    async def _acquire_token(self) -> str:
        """Acquire new token asynchronously."""
        oauth_token = await self.provider.acquire_token()

        self._cached_token = oauth_token.access_token
        self._token_expiry = datetime.now(timezone.utc) + timedelta(
            seconds=oauth_token.expires_in
        )

        return self._cached_token
```

**Note:** Full async refactoring requires:
- Async-compatible Orthanc plugin API (may not be available)
- Refactoring all HTTP request handling to async
- Testing with asyncio event loop
- Significant testing effort

**Recommendation:** Only implement if you have:
- High concurrency requirements (100+ requests/sec)
- Orthanc support for async plugins
- Dedicated 2+ weeks for implementation and testing

#### Success Criteria

- ✅ Async providers implemented
- ✅ Async token manager working
- ✅ Performance improvement demonstrated (10x+ throughput)
- ✅ All tests pass
- ✅ Backward compatibility maintained

---

### 3.2 Implement Hot Configuration Reload (3-5 days)

**Issue:** Configuration changes require restart
**Impact:** Downtime for config updates

#### Implementation Steps

**Step 1: Add file watcher**

```python
# src/config_watcher.py (NEW FILE)
"""Configuration file watcher for hot reload."""
import os
import threading
import time
from typing import Callable
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from src.structured_logger import structured_logger


class ConfigFileHandler(FileSystemEventHandler):
    """Handle configuration file changes."""

    def __init__(self, config_path: str, on_change: Callable):
        self.config_path = config_path
        self.on_change = on_change
        self.last_modified = 0

    def on_modified(self, event):
        """Called when config file is modified."""
        if event.src_path != self.config_path:
            return

        # Debounce: ignore if modified within last second
        current_time = time.time()
        if current_time - self.last_modified < 1.0:
            return

        self.last_modified = current_time

        structured_logger.info(
            "Configuration file changed",
            file=event.src_path,
        )

        try:
            self.on_change()
        except Exception as e:
            structured_logger.error(
                "Failed to reload configuration",
                error=str(e),
            )


class ConfigWatcher:
    """
    Watch configuration file for changes and reload.

    Enables hot configuration reload without restarting Orthanc.
    """

    def __init__(self, config_path: str, on_change: Callable):
        """
        Initialize config watcher.

        Args:
            config_path: Path to configuration file
            on_change: Callback when config changes
        """
        self.config_path = os.path.abspath(config_path)
        self.on_change = on_change

        self.observer = Observer()
        self.handler = ConfigFileHandler(self.config_path, on_change)

        # Watch directory containing config file
        watch_dir = os.path.dirname(self.config_path)
        self.observer.schedule(self.handler, watch_dir, recursive=False)

    def start(self):
        """Start watching for changes."""
        self.observer.start()
        structured_logger.info(
            "Config watcher started",
            file=self.config_path,
        )

    def stop(self):
        """Stop watching."""
        self.observer.stop()
        self.observer.join()
        structured_logger.info("Config watcher stopped")
```

**Step 2: Implement config reload logic**

```python
# src/plugin_context.py (MODIFIED)
class PluginContext:
    def __init__(self):
        # ... existing fields ...
        self.config_watcher: Optional[ConfigWatcher] = None
        self.reload_lock = threading.Lock()

    def reload_configuration(self, orthanc_module):
        """
        Reload configuration from Orthanc.

        This is called when the config file changes.
        """
        with self.reload_lock:
            structured_logger.info("Reloading OAuth configuration")

            try:
                # Load new configuration
                config = orthanc_module.GetConfiguration()
                parser = ConfigParser(config)
                new_servers = parser.get_servers()

                # Determine what changed
                old_servers = set(self.token_managers.keys())
                new_server_names = set(new_servers.keys())

                # Removed servers
                removed = old_servers - new_server_names
                for server_name in removed:
                    structured_logger.info(
                        "Removing OAuth server",
                        server=server_name,
                    )
                    self.token_manager_cache.remove(server_name)
                    del self.server_urls[server_name]

                # Added servers
                added = new_server_names - old_servers
                for server_name in added:
                    structured_logger.info(
                        "Adding OAuth server",
                        server=server_name,
                    )
                    server_config = new_servers[server_name]
                    manager = TokenManager(server_name, server_config)
                    self.register_token_manager(
                        server_name=server_name,
                        manager=manager,
                        url=server_config["Url"]
                    )

                # Updated servers
                updated = old_servers & new_server_names
                for server_name in updated:
                    old_url = self.server_urls.get(server_name)
                    new_url = new_servers[server_name]["Url"]

                    if old_url != new_url:
                        structured_logger.info(
                            "Updating OAuth server",
                            server=server_name,
                            old_url=old_url,
                            new_url=new_url,
                        )
                        # Recreate token manager with new config
                        server_config = new_servers[server_name]
                        manager = TokenManager(server_name, server_config)
                        self.register_token_manager(
                            server_name=server_name,
                            manager=manager,
                            url=new_url
                        )

                structured_logger.info(
                    "Configuration reloaded successfully",
                    servers=len(new_servers),
                    added=len(added),
                    removed=len(removed),
                    updated=len(updated),
                )

            except Exception as e:
                structured_logger.error(
                    "Failed to reload configuration",
                    error=str(e),
                )
                raise
```

**Step 3: Enable config watching**

```python
# src/dicomweb_oauth_plugin.py (MODIFIED)
def initialize_plugin(orthanc_module=None, context: Optional[PluginContext] = None):
    """Initialize plugin with optional config watching."""
    # ... existing initialization ...

    # Enable config watching if configured
    config = orthanc_module.GetConfiguration()
    oauth_config = config.get("DicomWebOAuth", {})

    if oauth_config.get("EnableConfigReload", False):
        config_path = oauth_config.get("ConfigPath", "/etc/orthanc/orthanc.json")

        def on_config_change():
            context.reload_configuration(orthanc_module)

        context.config_watcher = ConfigWatcher(config_path, on_config_change)
        context.config_watcher.start()

        logger.info("Configuration hot reload enabled")
```

**Step 4: Add configuration**

```json
// docker/orthanc.json
{
  "DicomWebOAuth": {
    "EnableConfigReload": true,  // ✅ Enable hot reload
    "ConfigPath": "/etc/orthanc/orthanc.json",
    "Servers": { ... }
  }
}
```

**Step 5: Add reload REST API endpoint**

```python
# src/dicomweb_oauth_plugin.py (ADD)
def handle_rest_api_reload(output, uri, **request) -> None:
    """POST /dicomweb-oauth/reload - Manually reload configuration"""
    context = get_plugin_context()

    try:
        context.reload_configuration(orthanc)

        result = {
            "status": "success",
            "message": "Configuration reloaded",
            "servers": len(context.token_managers),
        }
        output.AnswerBuffer(json.dumps(result, indent=2), "application/json")

    except Exception as e:
        result = {
            "status": "error",
            "message": str(e),
        }
        output.AnswerBuffer(
            json.dumps(result, indent=2),
            "application/json",
            status=500
        )


orthanc.RegisterRestCallback("/dicomweb-oauth/reload", handle_rest_api_reload)
```

#### Testing

```python
# tests/test_config_reload.py (NEW FILE)
import json
import os
import tempfile
import time
from src.config_watcher import ConfigWatcher


def test_config_file_change_detected():
    """Test that config file changes are detected."""
    # Create temporary config file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        config_path = f.name
        json.dump({"test": "initial"}, f)

    try:
        # Track callback calls
        callback_called = [False]

        def on_change():
            callback_called[0] = True

        # Start watcher
        watcher = ConfigWatcher(config_path, on_change)
        watcher.start()

        # Modify file
        time.sleep(0.5)
        with open(config_path, 'w') as f:
            json.dump({"test": "modified"}, f)

        # Wait for detection
        time.sleep(2)

        # Verify callback called
        assert callback_called[0], "Config change not detected"

        watcher.stop()

    finally:
        os.unlink(config_path)
```

#### Success Criteria

- ✅ Config changes detected automatically
- ✅ Configuration reloaded without restart
- ✅ Manual reload endpoint works
- ✅ No disruption to ongoing requests
- ✅ Thread-safe reload

---

## Implementation Timeline

```
Week 1: Priority 1 (High Impact, Low Effort)
├── Day 1: Pin dependencies + Add JWT library
├── Day 2: Implement dependency injection
├── Day 3-4: Structured logging
└── Day 5: Testing & documentation

Week 2-3: Priority 2.1-2.3
├── Days 1-3: Provider factory pattern
├── Day 4: Connection pooling
└── Day 5: Token cache limits

Week 4: Priority 2.4-2.5
├── Days 1-2: Circuit breaker
└── Days 3-5: Vulnerability scanning + Integration testing

Week 5-8: Priority 3 (Optional)
├── Async/await refactoring (if needed)
└── Hot config reload (if needed)
```

---

## Testing Strategy

### Unit Tests

Each component must have comprehensive unit tests:

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=term-missing --cov-report=html

# Target: 90% coverage for new code
```

### Integration Tests

Test full flow with real OAuth providers:

```bash
# Run integration tests
./scripts/integration-test.sh

# Test with each provider type:
- Generic OAuth2
- Azure AD
- (Future: Google, Keycloak)
```

### Performance Tests

Measure performance improvements:

```python
# tests/performance/test_latency.py
import time
import statistics

def test_token_acquisition_latency():
    """Measure token acquisition latency."""
    latencies = []

    for _ in range(100):
        start = time.time()
        token = token_manager.get_token()
        elapsed = time.time() - start
        latencies.append(elapsed)

    avg_latency = statistics.mean(latencies)
    p95_latency = statistics.quantiles(latencies, n=20)[18]  # 95th percentile

    # Assert performance targets
    assert avg_latency < 0.05, f"Average latency {avg_latency}s > 50ms"
    assert p95_latency < 0.10, f"P95 latency {p95_latency}s > 100ms"
```

### Load Tests

Test scalability improvements:

```bash
# Use locust for load testing
pip install locust==2.20.0

# tests/load/locustfile.py
from locust import HttpUser, task, between

class OAuthPluginUser(HttpUser):
    wait_time = between(0.1, 0.5)

    @task
    def get_status(self):
        self.client.get("/dicomweb-oauth/status")

    @task(3)
    def make_dicomweb_request(self):
        # Simulate DICOMweb request that triggers token injection
        self.client.get("/dicom-web/studies")

# Run load test
locust -f tests/load/locustfile.py --host http://localhost:8042
```

**Performance Targets:**
- Connection pooling: 20-50ms latency reduction
- Circuit breaker: Fast failure < 1ms when open
- Async (if implemented): 10x throughput improvement

---

## Migration Guide

### For Existing Users

**Version 1.0 → 2.0 Migration**

#### Breaking Changes

1. **Configuration format changes** (backward compatible):
   ```json
   // Old (still works):
   {
     "Servers": {
       "my-server": {
         "Url": "...",
         "TokenEndpoint": "...",
         "ClientId": "...",
         "ClientSecret": "..."
       }
     }
   }

   // New (recommended):
   {
     "Servers": {
       "my-server": {
         "ProviderType": "azure",  // Optional, auto-detected if omitted
         "Url": "...",
         "TokenEndpoint": "...",
         "TenantId": "...",  // Azure-specific
         "ClientId": "...",
         "ClientSecret": "..."
       }
     }
   }
   ```

2. **Log format changes** (opt-in):
   ```json
   {
     "DicomWebOAuth": {
       "LogFormat": "json",  // New: structured JSON logs
       "LogLevel": "INFO"    // New: configurable log level
     }
   }
   ```

#### Migration Steps

1. **Backup current configuration**:
   ```bash
   cp /etc/orthanc/orthanc.json /etc/orthanc/orthanc.json.backup
   ```

2. **Update plugin files**:
   ```bash
   # Stop Orthanc
   systemctl stop orthanc

   # Update plugin
   cp src/*.py /etc/orthanc/plugins/
   cp -r src/oauth_providers /etc/orthanc/plugins/

   # Update dependencies
   pip install -r requirements.lock
   ```

3. **Test configuration**:
   ```bash
   # Validate config (dry-run)
   python3 -c "
   from src.config_parser import ConfigParser
   import json

   with open('/etc/orthanc/orthanc.json') as f:
       config = json.load(f)

   parser = ConfigParser(config)
   servers = parser.get_servers()
   print(f'✅ Configuration valid: {len(servers)} servers')
   "
   ```

4. **Start Orthanc and verify**:
   ```bash
   # Start Orthanc
   systemctl start orthanc

   # Check plugin status
   curl http://localhost:8042/dicomweb-oauth/status

   # Check logs for errors
   journalctl -u orthanc -f
   ```

5. **Optional: Enable new features**:
   ```json
   {
     "DicomWebOAuth": {
       "LogFormat": "json",
       "EnableConfigReload": true,
       "MaxCachedServers": 100
     }
   }
   ```

---

## Success Criteria

### Overall Goals

- ✅ Architecture score: 72 → 85 (+13 points)
- ✅ Maintainability score: 58 → 80 (+22 points)
- ✅ Security score: 62 → 90 (+28 points)
- ✅ Overall score: 68.6 → 85 (+16.4 points)

### Technical Metrics

| Metric | Before | Target | Measurement |
|--------|--------|--------|-------------|
| Test coverage | 23.44% | 90% | pytest --cov |
| Cyclomatic complexity | 2.6 avg | < 5 avg | radon cc |
| Type hint coverage | 40% | 100% | mypy --strict |
| Memory leak | Unknown | None | stress testing |
| Token acquisition latency | ~200ms | < 150ms | performance tests |
| Vulnerability count | Unknown | 0 critical | safety + pip-audit |
| Circuit breaker activation | N/A | < 1% of requests | metrics |

### Operational Metrics

| Metric | Target |
|--------|--------|
| Uptime | > 99.9% |
| MTTR (Mean Time to Recover) | < 5 minutes |
| Token acquisition success rate | > 99.5% |
| Cache hit rate | > 95% |
| Log processing time | < 10ms per entry |

### Documentation Completeness

- ✅ All public APIs documented
- ✅ Architecture decision records (ADRs) written
- ✅ Migration guide complete
- ✅ Runbook for operations
- ✅ Performance tuning guide

---

## Approval & Sign-off

| Stakeholder | Role | Status | Date | Signature |
|-------------|------|--------|------|-----------|
| [Name] | Product Owner | ☐ Approved | | |
| [Name] | Technical Lead | ☐ Approved | | |
| [Name] | Security Lead | ☐ Approved | | |
| [Name] | Operations Lead | ☐ Approved | | |

---

**Document Status:** Draft
**Next Review:** After Week 1 completion
**Feedback:** [Create GitHub Issue](https://github.com/[username]/orthanc-dicomweb-oauth/issues/new)
