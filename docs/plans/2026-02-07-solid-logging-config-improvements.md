# SOLID, Logging, and Configuration Improvements Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix SOLID principle violations, enhance structured logging with correlation IDs, and implement robust configuration management with validation and encryption.

**Architecture:**
- Inject HTTP client interface for testability (Dependency Inversion)
- Enhance structured logging with correlation IDs, secret redaction, and log rotation
- Add JSON Schema validation, configuration versioning, and encryption at rest

**Tech Stack:**
- Python 3.11+, pytest, responses, jsonschema, cryptography

---

## Task 1: Add HTTP Client Abstraction (Dependency Inversion)

**Goal:** Fix SOLID Dependency Inversion violation by abstracting HTTP client

**Files:**
- Create: `src/http_client.py`
- Create: `tests/test_http_client.py`
- Modify: `src/oauth_providers/base.py:35-45`
- Modify: `src/oauth_providers/generic.py`
- Modify: `src/oauth_providers/azure.py`

### Step 1: Write failing test for HTTP client interface

Create `tests/test_http_client.py`:

```python
"""Tests for HTTP client interface."""
import pytest
import requests

from src.http_client import HttpClient, HttpResponse, RequestsHttpClient


class TestHttpResponse:
    """Test HttpResponse dataclass."""

    def test_http_response_creation(self):
        response = HttpResponse(
            status_code=200,
            json_data={"access_token": "test"},
            text="response text",
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 200
        assert response.json_data == {"access_token": "test"}
        assert response.text == "response text"
        assert response.headers["Content-Type"] == "application/json"


class TestRequestsHttpClient:
    """Test default requests-based HTTP client."""

    def test_post_success(self, responses):
        responses.add(
            responses.POST,
            "https://login.example.com/token",
            json={"access_token": "test_token"},
            status=200,
        )

        client = RequestsHttpClient()
        response = client.post(
            url="https://login.example.com/token",
            data={"grant_type": "client_credentials"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            verify=True,
            timeout=30,
        )

        assert response.status_code == 200
        assert response.json_data == {"access_token": "test_token"}

    def test_post_timeout(self, responses):
        responses.add(
            responses.POST,
            "https://login.example.com/token",
            body=requests.Timeout(),
        )

        client = RequestsHttpClient()

        with pytest.raises(requests.Timeout):
            client.post(
                url="https://login.example.com/token",
                data={"grant_type": "client_credentials"},
                verify=True,
            )

    def test_get_success(self, responses):
        responses.add(
            responses.GET,
            "https://login.example.com/keys",
            json={"keys": [{"kid": "key1"}]},
            status=200,
        )

        client = RequestsHttpClient()
        response = client.get(
            url="https://login.example.com/keys", verify=True, timeout=10
        )

        assert response.status_code == 200
        assert response.json_data == {"keys": [{"kid": "key1"}]}
```

### Step 2: Run tests to verify they fail

Run: `pytest tests/test_http_client.py -v`

Expected: FAIL with "ModuleNotFoundError: No module named 'src.http_client'"

### Step 3: Create HTTP client interface and implementation

Create `src/http_client.py`:

```python
"""HTTP client abstraction for testability."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests


@dataclass
class HttpResponse:
    """HTTP response container."""

    status_code: int
    json_data: Optional[Dict[str, Any]] = None
    text: str = ""
    headers: Dict[str, str] = None

    def __post_init__(self):
        if self.headers is None:
            self.headers = {}


class HttpClient(ABC):
    """
    Abstract HTTP client interface.

    Allows dependency injection and testing without actual HTTP calls.
    """

    @abstractmethod
    def post(
        self,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        verify: bool = True,
        timeout: int = 30,
    ) -> HttpResponse:
        """
        Make HTTP POST request.

        Args:
            url: Target URL
            data: Form data (for x-www-form-urlencoded)
            json: JSON payload
            headers: HTTP headers
            verify: Verify SSL certificates
            timeout: Request timeout in seconds

        Returns:
            HttpResponse object

        Raises:
            requests.Timeout: If request times out
            requests.ConnectionError: If connection fails
            requests.RequestException: For other HTTP errors
        """
        pass

    @abstractmethod
    def get(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        verify: bool = True,
        timeout: int = 30,
    ) -> HttpResponse:
        """
        Make HTTP GET request.

        Args:
            url: Target URL
            headers: HTTP headers
            verify: Verify SSL certificates
            timeout: Request timeout in seconds

        Returns:
            HttpResponse object

        Raises:
            requests.Timeout: If request times out
            requests.ConnectionError: If connection fails
            requests.RequestException: For other HTTP errors
        """
        pass


class RequestsHttpClient(HttpClient):
    """Default HTTP client using requests library."""

    def __init__(self, session: Optional[requests.Session] = None):
        """
        Initialize HTTP client.

        Args:
            session: Optional requests Session for connection pooling
        """
        self.session = session or requests.Session()

    def post(
        self,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        verify: bool = True,
        timeout: int = 30,
    ) -> HttpResponse:
        """Make HTTP POST request."""
        response = self.session.post(
            url=url, data=data, json=json, headers=headers, verify=verify, timeout=timeout
        )
        response.raise_for_status()

        return HttpResponse(
            status_code=response.status_code,
            json_data=response.json() if response.content else None,
            text=response.text,
            headers=dict(response.headers),
        )

    def get(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        verify: bool = True,
        timeout: int = 30,
    ) -> HttpResponse:
        """Make HTTP GET request."""
        response = self.session.get(url=url, headers=headers, verify=verify, timeout=timeout)
        response.raise_for_status()

        return HttpResponse(
            status_code=response.status_code,
            json_data=response.json() if response.content else None,
            text=response.text,
            headers=dict(response.headers),
        )
```

### Step 4: Run tests to verify they pass

Run: `pytest tests/test_http_client.py -v`

Expected: PASS (all tests green)

### Step 5: Commit HTTP client abstraction

```bash
git add src/http_client.py tests/test_http_client.py
git commit -m "feat: add HTTP client abstraction for dependency injection

- Create HttpClient interface and RequestsHttpClient implementation
- Fixes Dependency Inversion Principle violation
- Enables testability without monkey patching
- Adds connection pooling via requests.Session

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 2: Inject HTTP Client into OAuth Providers

**Goal:** Use HTTP client abstraction in OAuth providers

**Files:**
- Modify: `src/oauth_providers/base.py:35-45`
- Modify: `src/oauth_providers/generic.py`
- Modify: `src/oauth_providers/azure.py`
- Modify: `tests/test_oauth_providers.py`

### Step 1: Write failing test for HTTP client injection

Add to `tests/test_oauth_providers.py`:

```python
"""Test HTTP client injection in providers."""
from unittest.mock import Mock

from src.http_client import HttpClient, HttpResponse
from src.oauth_providers.base import OAuthConfig, OAuthToken
from src.oauth_providers.generic import GenericOAuthProvider


def test_generic_provider_with_mock_http_client():
    """Test provider with injected mock HTTP client."""
    # Create mock HTTP client
    mock_client = Mock(spec=HttpClient)
    mock_client.post.return_value = HttpResponse(
        status_code=200,
        json_data={
            "access_token": "test_token",
            "expires_in": 3600,
            "token_type": "Bearer",
        },
    )

    # Create provider with mock client
    config = OAuthConfig(
        token_endpoint="https://login.example.com/token",
        client_id="test_client",
        client_secret="test_secret",
        scope="api",
    )

    provider = GenericOAuthProvider(config=config, http_client=mock_client)

    # Acquire token
    token = provider.acquire_token()

    # Verify mock was called correctly
    mock_client.post.assert_called_once()
    call_args = mock_client.post.call_args

    assert call_args.kwargs["url"] == "https://login.example.com/token"
    assert "grant_type" in call_args.kwargs["data"]
    assert call_args.kwargs["data"]["grant_type"] == "client_credentials"

    # Verify token returned
    assert token.access_token == "test_token"
    assert token.expires_in == 3600
```

### Step 2: Run test to verify it fails

Run: `pytest tests/test_oauth_providers.py::test_generic_provider_with_mock_http_client -v`

Expected: FAIL with "GenericOAuthProvider.__init__() got an unexpected keyword argument 'http_client'"

### Step 3: Update OAuthProvider base class

Edit `src/oauth_providers/base.py`:

```python
"""Base OAuth provider interface."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from src.http_client import HttpClient


class TokenAcquisitionError(Exception):
    """Raised when token acquisition fails."""

    pass


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

    def __init__(self, config: OAuthConfig, http_client: Optional["HttpClient"] = None):
        """
        Initialize OAuth provider.

        Args:
            config: OAuth configuration
            http_client: Optional HTTP client (defaults to RequestsHttpClient)
        """
        self.config = config
        self._http_client = http_client

    @property
    def http_client(self) -> "HttpClient":
        """Get HTTP client, creating default if needed."""
        if self._http_client is None:
            from src.http_client import RequestsHttpClient

            self._http_client = RequestsHttpClient()
        return self._http_client

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

### Step 4: Update GenericOAuthProvider to use HTTP client

Read current `src/oauth_providers/generic.py` first, then update the `acquire_token` method:

```python
def acquire_token(self) -> OAuthToken:
    """Acquire token using client credentials flow."""
    try:
        # Use injected HTTP client instead of requests directly
        response = self.http_client.post(
            url=self.config.token_endpoint,
            data={
                "grant_type": "client_credentials",
                "client_id": self.config.client_id,
                "client_secret": self.config.client_secret,
                "scope": self.config.scope,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            verify=self.config.verify_ssl,
            timeout=30,
        )

        # Parse token from response
        token_data = response.json_data

        if not token_data or "access_token" not in token_data:
            raise TokenAcquisitionError("Invalid token response: missing access_token")

        return OAuthToken(
            access_token=token_data["access_token"],
            expires_in=token_data.get("expires_in", 3600),
            token_type=token_data.get("token_type", "Bearer"),
            refresh_token=token_data.get("refresh_token"),
            scope=token_data.get("scope"),
        )

    except requests.RequestException as e:
        raise TokenAcquisitionError(f"Failed to acquire token: {e}") from e
```

### Step 5: Update Azure provider similarly

Apply same HTTP client injection pattern to `src/oauth_providers/azure.py`

### Step 6: Run tests to verify they pass

Run: `pytest tests/test_oauth_providers.py -v`

Expected: PASS (all tests green including new injection test)

### Step 7: Commit HTTP client injection

```bash
git add src/oauth_providers/base.py src/oauth_providers/generic.py src/oauth_providers/azure.py tests/test_oauth_providers.py
git commit -m "refactor: inject HTTP client into OAuth providers

- Add http_client parameter to OAuthProvider base class
- Update GenericOAuthProvider and AzureOAuthProvider
- Enable testing without monkey patching
- Fixes Dependency Inversion Principle violation (SOLID)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 3: Add Correlation IDs to Structured Logging

**Goal:** Add request correlation tracking across log entries

**Files:**
- Modify: `src/structured_logger.py:18-24`
- Create: `tests/test_correlation_ids.py`
- Modify: `src/dicomweb_oauth_plugin.py` (add correlation ID generation)

### Step 1: Write failing test for correlation IDs

Create `tests/test_correlation_ids.py`:

```python
"""Tests for correlation ID tracking."""
import json
import logging
from io import StringIO

from src.structured_logger import StructuredLogger


def test_correlation_id_in_logs():
    """Test that correlation ID appears in all log entries."""
    # Create logger with string stream
    stream = StringIO()
    logger = StructuredLogger(name="test-correlation")
    logger.logger.handlers[0].stream = stream

    # Set correlation ID
    logger.set_correlation_id("req-123")

    # Log multiple entries
    logger.info("First log entry", operation="test")
    logger.warning("Second log entry", operation="test")
    logger.error("Third log entry", operation="test")

    # Parse JSON log output
    log_output = stream.getvalue()
    log_lines = [line for line in log_output.strip().split("\n") if line]
    log_entries = [json.loads(line) for line in log_lines]

    # All entries should have correlation ID
    assert len(log_entries) == 3
    for entry in log_entries:
        assert entry["correlation_id"] == "req-123"


def test_correlation_id_cleared():
    """Test that correlation ID can be cleared."""
    stream = StringIO()
    logger = StructuredLogger(name="test-clear")
    logger.logger.handlers[0].stream = stream

    # Set and clear correlation ID
    logger.set_correlation_id("req-456")
    logger.clear_correlation_id()

    # Log entry
    logger.info("Log without correlation ID")

    # Parse JSON log output
    log_output = stream.getvalue()
    log_entry = json.loads(log_output.strip())

    # Should not have correlation ID
    assert "correlation_id" not in log_entry


def test_auto_generate_correlation_id():
    """Test automatic correlation ID generation."""
    logger = StructuredLogger(name="test-auto")

    # Generate correlation ID
    correlation_id = logger.generate_correlation_id()

    # Should be UUID format
    assert len(correlation_id) == 36  # UUID4 format
    assert correlation_id.count("-") == 4
```

### Step 2: Run tests to verify they fail

Run: `pytest tests/test_correlation_ids.py -v`

Expected: FAIL with "AttributeError: 'StructuredLogger' object has no attribute 'set_correlation_id'"

### Step 3: Add correlation ID support to StructuredLogger

Edit `src/structured_logger.py`:

```python
"""Structured logging for OAuth plugin."""
import json
import logging
import sys
import uuid
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
        self.correlation_id: Optional[str] = None
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

    def set_correlation_id(self, correlation_id: str):
        """
        Set correlation ID for request tracking.

        Args:
            correlation_id: Unique identifier for request tracing
        """
        self.correlation_id = correlation_id

    def clear_correlation_id(self):
        """Clear correlation ID."""
        self.correlation_id = None

    def generate_correlation_id(self) -> str:
        """
        Generate a new correlation ID.

        Returns:
            UUID4 string
        """
        return str(uuid.uuid4())

    def _log(self, level: int, message: str, **kwargs):
        """Internal log method with context."""
        extra_fields = {**self.context, **kwargs}

        # Add correlation ID if set
        if self.correlation_id:
            extra_fields["correlation_id"] = self.correlation_id

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

### Step 4: Run tests to verify they pass

Run: `pytest tests/test_correlation_ids.py -v`

Expected: PASS (all tests green)

### Step 5: Commit correlation ID support

```bash
git add src/structured_logger.py tests/test_correlation_ids.py
git commit -m "feat: add correlation ID support to structured logging

- Add set_correlation_id() and generate_correlation_id() methods
- Correlation IDs appear in all log entries within request context
- Enables distributed tracing and log correlation
- Addresses logging gap: correlation IDs across log entries

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 4: Add Secret Redaction to Logging

**Goal:** Prevent sensitive data from being logged

**Files:**
- Modify: `src/structured_logger.py:90-110`
- Create: `tests/test_secret_redaction.py`

### Step 1: Write failing test for secret redaction

Create `tests/test_secret_redaction.py`:

```python
"""Tests for secret redaction in logs."""
import json
import re
from io import StringIO

from src.structured_logger import StructuredLogger, redact_secrets


def test_redact_secrets_in_string():
    """Test secret redaction in plain strings."""
    # Test various secret patterns
    test_cases = [
        (
            "client_secret=abc123xyz",
            "client_secret=***REDACTED***",
        ),
        (
            "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test",
            "Bearer ***REDACTED***",
        ),
        (
            "Authorization: Bearer token123",
            "Authorization: Bearer ***REDACTED***",
        ),
        (
            "password: my_secret_pass",
            "password: ***REDACTED***",
        ),
        (
            "api_key=sk_live_123456",
            "api_key=***REDACTED***",
        ),
    ]

    for original, expected in test_cases:
        result = redact_secrets(original)
        assert result == expected, f"Failed for: {original}"


def test_redact_secrets_in_dict():
    """Test secret redaction in dictionaries."""
    data = {
        "client_id": "public_client",
        "client_secret": "super_secret_123",
        "access_token": "eyJhbGci...",
        "username": "test_user",
        "password": "my_password",
    }

    redacted = redact_secrets(data)

    assert redacted["client_id"] == "public_client"  # Not redacted
    assert redacted["client_secret"] == "***REDACTED***"
    assert redacted["access_token"] == "***REDACTED***"
    assert redacted["username"] == "test_user"  # Not redacted
    assert redacted["password"] == "***REDACTED***"


def test_structured_logger_redacts_secrets():
    """Test that structured logger redacts secrets automatically."""
    stream = StringIO()
    logger = StructuredLogger(name="test-redact")
    logger.logger.handlers[0].stream = stream

    # Log entry with secrets
    logger.error(
        "Token acquisition failed",
        error="Invalid client_secret=abc123xyz",
        token="Bearer eyJhbGci...",
    )

    # Parse log output
    log_output = stream.getvalue()
    log_entry = json.loads(log_output.strip())

    # Secrets should be redacted
    assert "client_secret=***REDACTED***" in log_entry["error"]
    assert log_entry["token"] == "***REDACTED***"
    assert "abc123xyz" not in log_output
    assert "eyJhbGci" not in log_output
```

### Step 2: Run tests to verify they fail

Run: `pytest tests/test_secret_redaction.py -v`

Expected: FAIL with "NameError: name 'redact_secrets' is not defined"

### Step 3: Implement secret redaction

Edit `src/structured_logger.py`:

```python
"""Structured logging for OAuth plugin with secret redaction."""
import json
import logging
import re
import sys
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Union


# Secret patterns to redact
SECRET_PATTERNS = [
    (re.compile(r"(client_secret|api_key|password|secret|token)[\s=:]+[\w\-\.]+", re.IGNORECASE), r"\1=***REDACTED***"),
    (re.compile(r"Bearer\s+[\w\-\.]+", re.IGNORECASE), "Bearer ***REDACTED***"),
    (re.compile(r"Authorization:\s*Bearer\s+[\w\-\.]+", re.IGNORECASE), "Authorization: Bearer ***REDACTED***"),
]

# Keys to redact in dictionaries
REDACT_KEYS = {
    "client_secret",
    "secret",
    "password",
    "api_key",
    "access_token",
    "refresh_token",
    "token",
    "authorization",
}


def redact_secrets(value: Any) -> Any:
    """
    Redact secrets from log values.

    Args:
        value: Value to redact (string, dict, list, etc.)

    Returns:
        Value with secrets redacted
    """
    if isinstance(value, str):
        # Apply regex patterns to redact secrets in strings
        result = value
        for pattern, replacement in SECRET_PATTERNS:
            result = pattern.sub(replacement, result)
        return result

    elif isinstance(value, dict):
        # Redact dictionary values with sensitive keys
        return {
            key: "***REDACTED***" if key.lower() in REDACT_KEYS else redact_secrets(val)
            for key, val in value.items()
        }

    elif isinstance(value, (list, tuple)):
        # Recursively redact list/tuple items
        return type(value)(redact_secrets(item) for item in value)

    else:
        # Return non-string types as-is
        return value


class StructuredLogger:
    """
    Structured logger that outputs JSON-formatted log entries.

    Each log entry includes:
    - timestamp (ISO 8601)
    - level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    - message
    - context fields (server, operation, etc.)
    - correlation_id (for request tracing)

    Secrets are automatically redacted from all log entries.
    """

    def __init__(self, name: str = "oauth-plugin"):
        self.logger = logging.getLogger(name)
        self.context: Dict[str, Any] = {}
        self.correlation_id: Optional[str] = None
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

    def set_correlation_id(self, correlation_id: str):
        """
        Set correlation ID for request tracking.

        Args:
            correlation_id: Unique identifier for request tracing
        """
        self.correlation_id = correlation_id

    def clear_correlation_id(self):
        """Clear correlation ID."""
        self.correlation_id = None

    def generate_correlation_id(self) -> str:
        """
        Generate a new correlation ID.

        Returns:
            UUID4 string
        """
        return str(uuid.uuid4())

    def _log(self, level: int, message: str, **kwargs):
        """Internal log method with context and secret redaction."""
        extra_fields = {**self.context, **kwargs}

        # Add correlation ID if set
        if self.correlation_id:
            extra_fields["correlation_id"] = self.correlation_id

        # Redact secrets from message and fields
        redacted_message = redact_secrets(message)
        redacted_fields = redact_secrets(extra_fields)

        self.logger.log(level, redacted_message, extra={"fields": redacted_fields})

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

### Step 4: Run tests to verify they pass

Run: `pytest tests/test_secret_redaction.py -v`

Expected: PASS (all tests green)

### Step 5: Commit secret redaction

```bash
git add src/structured_logger.py tests/test_secret_redaction.py
git commit -m "feat: add automatic secret redaction to logging

- Redact client_secret, api_key, password, token from logs
- Apply regex patterns to catch various secret formats
- Prevents sensitive data leakage in error messages
- Addresses logging security gap

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 5: Add Configuration Schema Validation

**Goal:** Validate configuration using JSON Schema

**Files:**
- Create: `src/config_schema.py`
- Create: `tests/test_config_validation.py`
- Modify: `src/config_parser.py:24-35`
- Create: `schemas/config-schema.json`

### Step 1: Write failing test for schema validation

Create `tests/test_config_validation.py`:

```python
"""Tests for configuration schema validation."""
import pytest

from src.config_parser import ConfigError, ConfigParser


def test_valid_config_passes_validation():
    """Test that valid configuration passes schema validation."""
    config = {
        "DicomWebOAuth": {
            "Servers": {
                "server1": {
                    "Url": "https://pacs.example.com/dicomweb",
                    "TokenEndpoint": "https://login.example.com/token",
                    "ClientId": "client123",
                    "ClientSecret": "secret456",
                    "Scope": "api",
                    "VerifySSL": True,
                }
            }
        }
    }

    parser = ConfigParser(config)
    servers = parser.get_servers()

    assert "server1" in servers
    assert servers["server1"]["ClientId"] == "client123"


def test_missing_required_field_fails_validation():
    """Test that missing required fields fail validation."""
    config = {
        "DicomWebOAuth": {
            "Servers": {
                "server1": {
                    "Url": "https://pacs.example.com/dicomweb",
                    "TokenEndpoint": "https://login.example.com/token",
                    # Missing ClientId and ClientSecret
                    "Scope": "api",
                }
            }
        }
    }

    with pytest.raises(ConfigError) as exc_info:
        ConfigParser(config)

    assert "ClientId" in str(exc_info.value) or "required" in str(exc_info.value).lower()


def test_invalid_type_fails_validation():
    """Test that invalid field types fail validation."""
    config = {
        "DicomWebOAuth": {
            "Servers": {
                "server1": {
                    "Url": "https://pacs.example.com/dicomweb",
                    "TokenEndpoint": "https://login.example.com/token",
                    "ClientId": "client123",
                    "ClientSecret": "secret456",
                    "VerifySSL": "yes",  # Should be boolean
                }
            }
        }
    }

    with pytest.raises(ConfigError) as exc_info:
        ConfigParser(config)

    assert "VerifySSL" in str(exc_info.value) or "boolean" in str(exc_info.value).lower()


def test_invalid_url_format_fails_validation():
    """Test that invalid URLs fail validation."""
    config = {
        "DicomWebOAuth": {
            "Servers": {
                "server1": {
                    "Url": "not-a-valid-url",
                    "TokenEndpoint": "also-invalid",
                    "ClientId": "client123",
                    "ClientSecret": "secret456",
                }
            }
        }
    }

    with pytest.raises(ConfigError) as exc_info:
        ConfigParser(config)

    assert "url" in str(exc_info.value).lower() or "format" in str(exc_info.value).lower()
```

### Step 2: Run tests to verify they fail

Run: `pytest tests/test_config_validation.py -v`

Expected: PASS on first test, but no validation errors on invalid configs (tests 2-4 fail)

### Step 3: Create JSON Schema

Create `schemas/config-schema.json`:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Orthanc DICOMweb OAuth Configuration",
  "description": "JSON Schema for validating DICOMweb OAuth plugin configuration",
  "type": "object",
  "required": ["DicomWebOAuth"],
  "properties": {
    "DicomWebOAuth": {
      "type": "object",
      "required": ["Servers"],
      "properties": {
        "Servers": {
          "type": "object",
          "minProperties": 1,
          "additionalProperties": {
            "$ref": "#/definitions/ServerConfig"
          }
        }
      }
    }
  },
  "definitions": {
    "ServerConfig": {
      "type": "object",
      "required": ["Url", "TokenEndpoint", "ClientId", "ClientSecret"],
      "properties": {
        "Url": {
          "type": "string",
          "format": "uri",
          "pattern": "^https?://",
          "description": "DICOMweb server URL"
        },
        "TokenEndpoint": {
          "type": "string",
          "format": "uri",
          "pattern": "^https?://",
          "description": "OAuth2 token endpoint URL"
        },
        "ClientId": {
          "type": "string",
          "minLength": 1,
          "description": "OAuth2 client ID"
        },
        "ClientSecret": {
          "type": "string",
          "minLength": 1,
          "description": "OAuth2 client secret"
        },
        "Scope": {
          "type": "string",
          "description": "OAuth2 scope"
        },
        "VerifySSL": {
          "type": "boolean",
          "default": true,
          "description": "Verify SSL certificates"
        },
        "TokenRefreshBufferSeconds": {
          "type": "integer",
          "minimum": 0,
          "maximum": 3600,
          "default": 300,
          "description": "Token refresh buffer in seconds"
        },
        "ProviderType": {
          "type": "string",
          "enum": ["auto", "azure", "google", "keycloak", "generic"],
          "default": "auto",
          "description": "OAuth provider type"
        }
      },
      "additionalProperties": false
    }
  }
}
```

### Step 4: Create config schema validator

Create `src/config_schema.py`:

```python
"""Configuration schema validation."""
import json
import os
from pathlib import Path
from typing import Any, Dict

try:
    import jsonschema
    from jsonschema import ValidationError

    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False
    ValidationError = Exception  # Fallback


def get_schema_path() -> Path:
    """Get path to configuration schema file."""
    # Schema is in schemas/ directory at project root
    current_file = Path(__file__)
    project_root = current_file.parent.parent
    return project_root / "schemas" / "config-schema.json"


def load_schema() -> Dict[str, Any]:
    """
    Load configuration schema from file.

    Returns:
        Schema dictionary

    Raises:
        FileNotFoundError: If schema file not found
    """
    schema_path = get_schema_path()

    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    with open(schema_path, "r") as f:
        return json.load(f)


def validate_config(config: Dict[str, Any]) -> None:
    """
    Validate configuration against JSON Schema.

    Args:
        config: Configuration dictionary to validate

    Raises:
        ValidationError: If configuration is invalid
        ImportError: If jsonschema library not installed
    """
    if not JSONSCHEMA_AVAILABLE:
        raise ImportError(
            "jsonschema library required for validation. "
            "Install with: pip install jsonschema"
        )

    schema = load_schema()

    try:
        jsonschema.validate(instance=config, schema=schema)
    except ValidationError as e:
        # Make error message more user-friendly
        error_path = " -> ".join(str(p) for p in e.path) if e.path else "root"
        raise ValidationError(
            f"Configuration validation failed at '{error_path}': {e.message}"
        ) from e
```

### Step 5: Integrate schema validation into ConfigParser

Edit `src/config_parser.py`:

```python
"""Configuration parser for DICOMweb OAuth plugin."""
import os
import re
from typing import Any, Dict

from src.config_schema import validate_config


class ConfigError(Exception):
    """Raised when configuration is invalid."""

    pass


class ConfigParser:
    """Parse and validate plugin configuration from Orthanc JSON config."""

    def __init__(self, config: Dict[str, Any], validate_schema: bool = True):
        """
        Initialize parser with Orthanc configuration.

        Args:
            config: Full Orthanc configuration dict
            validate_schema: Whether to validate against JSON Schema (default True)
        """
        self.config = config
        self._validate_config(validate_schema=validate_schema)

    def _validate_config(self, validate_schema: bool = True) -> None:
        """
        Validate that required configuration structure exists.

        Args:
            validate_schema: Whether to validate against JSON Schema
        """
        if "DicomWebOAuth" not in self.config:
            raise ConfigError("Missing 'DicomWebOAuth' section in configuration")

        if "Servers" not in self.config["DicomWebOAuth"]:
            raise ConfigError(
                "Missing 'Servers' section in DicomWebOAuth configuration"
            )

        # Validate against JSON Schema if enabled
        if validate_schema:
            try:
                validate_config(self.config)
            except Exception as e:
                raise ConfigError(f"Configuration validation failed: {e}") from e

    def get_servers(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all configured DICOMweb servers with OAuth settings.

        Returns:
            Dictionary mapping server names to their configurations
        """
        servers = self.config["DicomWebOAuth"]["Servers"]
        processed_servers = {}

        for name, server_config in servers.items():
            processed_servers[name] = self._process_server_config(server_config)

        return processed_servers

    def _process_server_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single server configuration, applying env var substitution.

        Args:
            config: Raw server configuration

        Returns:
            Processed configuration with environment variables expanded
        """
        processed: Dict[str, Any] = {}
        for key, value in config.items():
            if isinstance(value, str):
                processed[key] = self._substitute_env_vars(value)
            else:
                processed[key] = value

        # SSL/TLS Verification (defaults to True for security)
        if "VerifySSL" not in processed:
            processed["VerifySSL"] = True

        return processed

    def _substitute_env_vars(self, value: str) -> str:
        """
        Replace ${VAR_NAME} patterns with environment variable values.

        Args:
            value: String that may contain ${VAR_NAME} patterns

        Returns:
            String with environment variables expanded

        Raises:
            ConfigError: If a referenced environment variable is not set
        """
        pattern = r"\$\{([^}]+)\}"

        def replace_var(match):
            var_name = match.group(1)
            if var_name not in os.environ:
                raise ConfigError(
                    f"Environment variable '{var_name}' referenced in config "
                    "but not set"
                )
            return os.environ[var_name]

        return re.sub(pattern, replace_var, value)
```

### Step 6: Add jsonschema to requirements

Edit `requirements.txt`:

```
requests>=2.31.0,<3.0.0
jsonschema>=4.20.0,<5.0.0
```

### Step 7: Run tests to verify they pass

Run: `pytest tests/test_config_validation.py -v`

Expected: PASS (all validation tests work correctly)

### Step 8: Commit configuration validation

```bash
git add schemas/config-schema.json src/config_schema.py src/config_parser.py tests/test_config_validation.py requirements.txt
git commit -m "feat: add JSON Schema validation for configuration

- Create comprehensive JSON Schema for config validation
- Integrate validation into ConfigParser
- Validate required fields, types, and URL formats
- Add jsonschema dependency
- Addresses configuration management gap

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 6: Add Configuration Versioning

**Goal:** Support configuration schema versioning for backward compatibility

**Files:**
- Modify: `schemas/config-schema.json`
- Create: `src/config_migration.py`
- Create: `tests/test_config_migration.py`

### Step 1: Write failing test for config migration

Create `tests/test_config_migration.py`:

```python
"""Tests for configuration versioning and migration."""
import pytest

from src.config_migration import detect_config_version, migrate_config


def test_detect_v1_config():
    """Test detection of v1 configuration."""
    config_v1 = {
        "DicomWebOAuth": {
            "Servers": {
                "server1": {
                    "Url": "https://pacs.example.com/dicomweb",
                    "TokenEndpoint": "https://login.example.com/token",
                    "ClientId": "client123",
                    "ClientSecret": "secret456",
                }
            }
        }
    }

    version = detect_config_version(config_v1)
    assert version == "1.0"


def test_detect_v2_config():
    """Test detection of v2 configuration with explicit version."""
    config_v2 = {
        "ConfigVersion": "2.0",
        "DicomWebOAuth": {
            "Servers": {
                "server1": {
                    "Url": "https://pacs.example.com/dicomweb",
                    "TokenEndpoint": "https://login.example.com/token",
                    "ClientId": "client123",
                    "ClientSecret": "secret456",
                    "ProviderType": "azure",
                }
            }
        },
    }

    version = detect_config_version(config_v2)
    assert version == "2.0"


def test_migrate_v1_to_v2():
    """Test migration from v1 to v2 configuration."""
    config_v1 = {
        "DicomWebOAuth": {
            "Servers": {
                "server1": {
                    "Url": "https://pacs.example.com/dicomweb",
                    "TokenEndpoint": "https://login.example.com/token",
                    "ClientId": "client123",
                    "ClientSecret": "secret456",
                }
            }
        }
    }

    migrated = migrate_config(config_v1)

    # Should have version field
    assert "ConfigVersion" in migrated
    assert migrated["ConfigVersion"] == "2.0"

    # Server config should be preserved
    assert "server1" in migrated["DicomWebOAuth"]["Servers"]

    # Should have default provider type
    server = migrated["DicomWebOAuth"]["Servers"]["server1"]
    assert "ProviderType" in server
    assert server["ProviderType"] == "auto"


def test_migrate_already_v2():
    """Test that v2 config is not modified."""
    config_v2 = {
        "ConfigVersion": "2.0",
        "DicomWebOAuth": {
            "Servers": {
                "server1": {
                    "Url": "https://pacs.example.com/dicomweb",
                    "TokenEndpoint": "https://login.example.com/token",
                    "ClientId": "client123",
                    "ClientSecret": "secret456",
                    "ProviderType": "azure",
                }
            }
        },
    }

    migrated = migrate_config(config_v2)

    # Should be unchanged
    assert migrated == config_v2
```

### Step 2: Run tests to verify they fail

Run: `pytest tests/test_config_migration.py -v`

Expected: FAIL with "ModuleNotFoundError: No module named 'src.config_migration'"

### Step 3: Create config migration module

Create `src/config_migration.py`:

```python
"""Configuration versioning and migration."""
import copy
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

# Current configuration version
CURRENT_VERSION = "2.0"


def detect_config_version(config: Dict[str, Any]) -> str:
    """
    Detect configuration version.

    Args:
        config: Configuration dictionary

    Returns:
        Version string (e.g., "1.0", "2.0")
    """
    # Explicit version field (v2+)
    if "ConfigVersion" in config:
        return config["ConfigVersion"]

    # No version field = v1.0
    return "1.0"


def migrate_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Migrate configuration to current version.

    Args:
        config: Configuration dictionary (any version)

    Returns:
        Migrated configuration at current version
    """
    current_version = detect_config_version(config)

    # Already at current version
    if current_version == CURRENT_VERSION:
        return config

    # Make a deep copy to avoid mutating original
    migrated = copy.deepcopy(config)

    # Apply migrations in sequence
    if current_version == "1.0":
        migrated = _migrate_v1_to_v2(migrated)
        logger.info("Migrated configuration from v1.0 to v2.0")

    return migrated


def _migrate_v1_to_v2(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Migrate v1.0 configuration to v2.0.

    Changes in v2.0:
    - Add ConfigVersion field
    - Add ProviderType field to servers (default: "auto")
    - Add TokenRefreshBufferSeconds default

    Args:
        config: v1.0 configuration

    Returns:
        v2.0 configuration
    """
    # Add version field
    config["ConfigVersion"] = "2.0"

    # Add defaults to each server
    if "DicomWebOAuth" in config and "Servers" in config["DicomWebOAuth"]:
        for server_name, server_config in config["DicomWebOAuth"]["Servers"].items():
            # Add ProviderType if missing
            if "ProviderType" not in server_config:
                server_config["ProviderType"] = "auto"

            # Add TokenRefreshBufferSeconds if missing
            if "TokenRefreshBufferSeconds" not in server_config:
                server_config["TokenRefreshBufferSeconds"] = 300

    return config
```

### Step 4: Integrate migration into ConfigParser

Edit `src/config_parser.py` to add migration:

```python
from src.config_migration import migrate_config

class ConfigParser:
    """Parse and validate plugin configuration from Orthanc JSON config."""

    def __init__(self, config: Dict[str, Any], validate_schema: bool = True):
        """
        Initialize parser with Orthanc configuration.

        Args:
            config: Full Orthanc configuration dict
            validate_schema: Whether to validate against JSON Schema (default True)
        """
        # Migrate config to current version
        self.config = migrate_config(config)
        self._validate_config(validate_schema=validate_schema)
```

### Step 5: Update JSON schema to include version

Edit `schemas/config-schema.json` to add ConfigVersion:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Orthanc DICOMweb OAuth Configuration",
  "description": "JSON Schema for validating DICOMweb OAuth plugin configuration",
  "type": "object",
  "required": ["DicomWebOAuth"],
  "properties": {
    "ConfigVersion": {
      "type": "string",
      "enum": ["2.0"],
      "description": "Configuration schema version"
    },
    "DicomWebOAuth": {
      ...
    }
  }
}
```

### Step 6: Run tests to verify they pass

Run: `pytest tests/test_config_migration.py -v`

Expected: PASS (all migration tests work)

### Step 7: Commit configuration versioning

```bash
git add src/config_migration.py src/config_parser.py schemas/config-schema.json tests/test_config_migration.py
git commit -m "feat: add configuration versioning and migration

- Add ConfigVersion field for schema versioning
- Implement v1.0 to v2.0 migration
- Auto-migrate on config load
- Ensures backward compatibility
- Addresses configuration management gap

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 7: Add Log Rotation Configuration

**Goal:** Configure log rotation to prevent disk space issues

**Files:**
- Create: `src/log_rotation.py`
- Create: `tests/test_log_rotation.py`
- Modify: `src/structured_logger.py:24-31`

### Step 1: Write failing test for log rotation

Create `tests/test_log_rotation.py`:

```python
"""Tests for log rotation configuration."""
import logging
import os
import tempfile
from pathlib import Path

from src.log_rotation import setup_rotating_file_handler


def test_rotating_file_handler_creates_log_file():
    """Test that rotating handler creates log file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = Path(tmpdir) / "test.log"

        logger = logging.getLogger("test-rotation")
        handler = setup_rotating_file_handler(
            filename=str(log_file), max_bytes=1024, backup_count=3
        )
        logger.addHandler(handler)

        # Write log entry
        logger.info("Test log entry")

        # Log file should exist
        assert log_file.exists()
        assert log_file.read_text().strip() != ""


def test_rotating_file_handler_rotates_on_size():
    """Test that logs rotate when reaching max size."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = Path(tmpdir) / "test.log"

        logger = logging.getLogger("test-rotation-size")
        handler = setup_rotating_file_handler(
            filename=str(log_file),
            max_bytes=100,  # Very small to trigger rotation
            backup_count=2,
        )
        logger.addHandler(handler)

        # Write many log entries to exceed max_bytes
        for i in range(50):
            logger.info(f"Log entry {i} with some padding text to increase size")

        # Should have rotated files
        assert log_file.exists()

        # Check for backup files
        backup1 = Path(str(log_file) + ".1")
        assert backup1.exists(), "Backup log file should exist after rotation"


def test_rotating_file_handler_limits_backup_count():
    """Test that backup count is respected."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = Path(tmpdir) / "test.log"

        logger = logging.getLogger("test-rotation-count")
        handler = setup_rotating_file_handler(
            filename=str(log_file), max_bytes=100, backup_count=2
        )
        logger.addHandler(handler)

        # Write many entries to trigger multiple rotations
        for i in range(200):
            logger.info(f"Log entry {i} with padding text to exceed size limit")

        # Should have at most 2 backup files (plus current)
        backup_files = list(Path(tmpdir).glob("test.log.*"))
        assert len(backup_files) <= 2, "Should not exceed backup_count"
```

### Step 2: Run tests to verify they fail

Run: `pytest tests/test_log_rotation.py -v`

Expected: FAIL with "ModuleNotFoundError: No module named 'src.log_rotation'"

### Step 3: Create log rotation module

Create `src/log_rotation.py`:

```python
"""Log rotation configuration."""
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional


def setup_rotating_file_handler(
    filename: str,
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB default
    backup_count: int = 5,
    formatter: Optional[logging.Formatter] = None,
) -> RotatingFileHandler:
    """
    Create a rotating file handler for logs.

    Args:
        filename: Path to log file
        max_bytes: Maximum bytes per file before rotation (default 10MB)
        backup_count: Number of backup files to keep (default 5)
        formatter: Optional log formatter

    Returns:
        Configured RotatingFileHandler
    """
    # Ensure log directory exists
    log_path = Path(filename)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Create rotating handler
    handler = RotatingFileHandler(
        filename=filename, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
    )

    # Set formatter if provided
    if formatter:
        handler.setFormatter(formatter)

    return handler


def configure_log_rotation(
    logger: logging.Logger,
    log_file: str,
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5,
    formatter: Optional[logging.Formatter] = None,
) -> None:
    """
    Configure log rotation for a logger.

    Args:
        logger: Logger instance to configure
        log_file: Path to log file
        max_bytes: Maximum bytes per file before rotation
        backup_count: Number of backup files to keep
        formatter: Optional log formatter
    """
    handler = setup_rotating_file_handler(
        filename=log_file,
        max_bytes=max_bytes,
        backup_count=backup_count,
        formatter=formatter,
    )

    logger.addHandler(handler)
```

### Step 4: Add rotation option to StructuredLogger

Edit `src/structured_logger.py`:

```python
from src.log_rotation import setup_rotating_file_handler

class StructuredLogger:
    """
    Structured logger that outputs JSON-formatted log entries.
    ...
    """

    def __init__(
        self,
        name: str = "oauth-plugin",
        log_file: Optional[str] = None,
        max_bytes: int = 10 * 1024 * 1024,
        backup_count: int = 5,
    ):
        """
        Initialize structured logger.

        Args:
            name: Logger name
            log_file: Optional file path for log rotation
            max_bytes: Max bytes per log file (default 10MB)
            backup_count: Number of backup files (default 5)
        """
        self.logger = logging.getLogger(name)
        self.context: Dict[str, Any] = {}
        self.correlation_id: Optional[str] = None
        self._setup_handler(log_file, max_bytes, backup_count)

    def _setup_handler(
        self, log_file: Optional[str], max_bytes: int, backup_count: int
    ):
        """Setup JSON formatter and handler(s)."""
        formatter = JsonFormatter()

        # Always add stdout handler
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setFormatter(formatter)
        self.logger.addHandler(stdout_handler)

        # Add file handler with rotation if specified
        if log_file:
            file_handler = setup_rotating_file_handler(
                filename=log_file,
                max_bytes=max_bytes,
                backup_count=backup_count,
                formatter=formatter,
            )
            self.logger.addHandler(file_handler)

        self.logger.setLevel(logging.INFO)
```

### Step 5: Run tests to verify they pass

Run: `pytest tests/test_log_rotation.py -v`

Expected: PASS (all rotation tests work)

### Step 6: Commit log rotation

```bash
git add src/log_rotation.py src/structured_logger.py tests/test_log_rotation.py
git commit -m "feat: add log rotation configuration

- Implement RotatingFileHandler for log files
- Configurable max file size and backup count
- Default 10MB per file, 5 backups
- Prevents disk space issues in production
- Addresses logging gap: log rotation

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 8: Final Testing and Documentation

**Goal:** Run comprehensive tests and update documentation

**Files:**
- Update: `docs/IMPROVEMENT-PLAN.md`
- Update: `README.md`
- Update: `CHANGELOG.md`

### Step 1: Run full test suite

Run: `pytest tests/ -v --cov=src --cov-report=term-missing`

Expected: All tests pass with improved coverage

### Step 2: Run integration tests

Run: `./tests/integration/run_integration_tests.sh`

Expected: Integration tests pass

### Step 3: Update improvement plan

Edit `docs/IMPROVEMENT-PLAN.md` to mark completed items:

- ✅ HTTP Client Abstraction (Dependency Inversion)
- ✅ Correlation IDs in Logging
- ✅ Secret Redaction in Logs
- ✅ Configuration Schema Validation
- ✅ Configuration Versioning
- ✅ Log Rotation Configuration

### Step 4: Update README with new features

Edit `README.md` to document:
- Structured logging with correlation IDs
- Automatic secret redaction
- Configuration schema validation
- Log rotation settings

### Step 5: Update CHANGELOG

Edit `CHANGELOG.md`:

```markdown
## [2.0.0] - 2026-02-07

### Added
- HTTP client abstraction for dependency injection and testability
- Correlation IDs for distributed tracing
- Automatic secret redaction in logs
- JSON Schema validation for configuration
- Configuration versioning and migration (v1.0 to v2.0)
- Log rotation with configurable size and backup count

### Changed
- OAuth providers now accept injected HTTP client
- Structured logger supports file output with rotation
- Configuration parser auto-migrates old configs

### Fixed
- SOLID Dependency Inversion Principle violation
- Logging gaps: correlation IDs, secret leakage, rotation
- Configuration management: validation, versioning
```

### Step 6: Commit documentation updates

```bash
git add docs/IMPROVEMENT-PLAN.md README.md CHANGELOG.md
git commit -m "docs: update documentation for v2.0 improvements

- Mark completed SOLID, logging, and config improvements
- Add feature documentation to README
- Update CHANGELOG with v2.0 changes

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

### Step 7: Create summary report

Create final summary report showing:
- SOLID score improvement
- Logging score improvement
- Configuration management score improvement
- Test coverage increase

---

## Execution Handoff

**Plan complete and saved to `docs/plans/2026-02-07-solid-logging-config-improvements.md`.**

**Two execution options:**

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

**Which approach would you prefer?**
