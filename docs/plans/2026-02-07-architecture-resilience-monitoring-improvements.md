# Architecture, Resilience, and Monitoring Improvements

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Eliminate global state anti-pattern, implement circuit breaker pattern with configurable retry strategies, add Prometheus metrics, enhance error handling with detailed error codes and actionable messages.

**Architecture:** Replace global state with singleton pattern, implement resilience patterns (circuit breaker, fallback), add comprehensive metrics collection with Prometheus endpoint, create structured error code system with troubleshooting guidance.

**Tech Stack:** Python 3.11+, prometheus-client, pybreaker (or custom implementation), requests, threading, dataclasses

---

## Task 1: Define Error Code System

**Files:**
- Create: `src/error_codes.py`
- Create: `tests/test_error_codes.py`

**Step 1: Write the failing test**

```python
# tests/test_error_codes.py
"""Tests for structured error code system."""
import pytest

from src.error_codes import (
    ErrorCode,
    ErrorCategory,
    ErrorSeverity,
    PluginError,
    ConfigurationError,
    TokenAcquisitionError,
    NetworkError,
)


def test_error_code_enum_values():
    """Test that error codes have proper structure."""
    assert ErrorCode.CONFIG_MISSING_KEY.value.startswith("CFG")
    assert ErrorCode.TOKEN_ACQUISITION_FAILED.value.startswith("TOK")
    assert ErrorCode.NETWORK_TIMEOUT.value.startswith("NET")


def test_error_category_mapping():
    """Test that error codes map to categories correctly."""
    assert ErrorCode.CONFIG_MISSING_KEY.category == ErrorCategory.CONFIGURATION
    assert ErrorCode.TOKEN_ACQUISITION_FAILED.category == ErrorCategory.AUTHENTICATION
    assert ErrorCode.NETWORK_TIMEOUT.category == ErrorCategory.NETWORK


def test_plugin_error_with_code():
    """Test PluginError includes error code and troubleshooting."""
    error = ConfigurationError(
        ErrorCode.CONFIG_MISSING_KEY,
        "Missing 'ClientId' in configuration",
        details={"server": "test-server", "missing_key": "ClientId"},
    )

    assert error.error_code == ErrorCode.CONFIG_MISSING_KEY
    assert error.http_status == 500
    assert "ClientId" in error.message
    assert error.details["server"] == "test-server"
    assert len(error.troubleshooting_steps) > 0
    assert error.documentation_url is not None


def test_error_to_dict():
    """Test error serialization for API responses."""
    error = NetworkError(
        ErrorCode.NETWORK_TIMEOUT,
        "Connection timeout to token endpoint",
        details={"endpoint": "https://login.example.com/token", "timeout": 30},
    )

    error_dict = error.to_dict()

    assert error_dict["error_code"] == "NET-001"
    assert error_dict["category"] == "NETWORK"
    assert error_dict["severity"] == "ERROR"
    assert error_dict["message"] == "Connection timeout to token endpoint"
    assert "troubleshooting" in error_dict
    assert "documentation_url" in error_dict
    assert error_dict["details"]["endpoint"] == "https://login.example.com/token"


def test_error_severity_levels():
    """Test different severity levels."""
    warning = PluginError(
        ErrorCode.TOKEN_REFRESH_RECOMMENDED,
        "Token expiring soon",
        severity=ErrorSeverity.WARNING,
    )

    critical = PluginError(
        ErrorCode.AUTH_PROVIDER_UNAVAILABLE,
        "Cannot reach authentication provider",
        severity=ErrorSeverity.CRITICAL,
    )

    assert warning.severity == ErrorSeverity.WARNING
    assert warning.http_status == 200
    assert critical.severity == ErrorSeverity.CRITICAL
    assert critical.http_status == 503
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_error_codes.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'src.error_codes'"

**Step 3: Write minimal implementation**

```python
# src/error_codes.py
"""Structured error code system for detailed error handling."""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ErrorCategory(str, Enum):
    """Error category for classification."""

    CONFIGURATION = "CONFIGURATION"
    AUTHENTICATION = "AUTHENTICATION"
    NETWORK = "NETWORK"
    AUTHORIZATION = "AUTHORIZATION"
    INTERNAL = "INTERNAL"


class ErrorSeverity(str, Enum):
    """Error severity levels."""

    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class ErrorCodeInfo:
    """Metadata for an error code."""

    code: str
    category: ErrorCategory
    severity: ErrorSeverity
    http_status: int
    description: str
    troubleshooting: List[str]
    documentation_url: str


class ErrorCode(Enum):
    """Enumeration of all error codes with metadata."""

    # Configuration Errors (CFG-xxx)
    CONFIG_MISSING_KEY = ErrorCodeInfo(
        code="CFG-001",
        category=ErrorCategory.CONFIGURATION,
        severity=ErrorSeverity.ERROR,
        http_status=500,
        description="Required configuration key is missing",
        troubleshooting=[
            "Check that all required keys are present in DicomWebOAuth.Servers config",
            "Required keys: Url, TokenEndpoint, ClientId, ClientSecret",
            "Verify configuration file syntax is valid JSON",
        ],
        documentation_url="https://github.com/rhavekost/orthanc-dicomweb-oauth/blob/main/docs/CONFIG.md#required-fields",
    )

    CONFIG_INVALID_VALUE = ErrorCodeInfo(
        code="CFG-002",
        category=ErrorCategory.CONFIGURATION,
        severity=ErrorSeverity.ERROR,
        http_status=500,
        description="Configuration value is invalid",
        troubleshooting=[
            "Verify that URLs are properly formatted (must start with http:// or https://)",
            "Check that numeric values are within valid ranges",
            "Ensure boolean values are true/false",
        ],
        documentation_url="https://github.com/rhavekost/orthanc-dicomweb-oauth/blob/main/docs/CONFIG.md#field-formats",
    )

    CONFIG_ENV_VAR_MISSING = ErrorCodeInfo(
        code="CFG-003",
        category=ErrorCategory.CONFIGURATION,
        severity=ErrorSeverity.ERROR,
        http_status=500,
        description="Referenced environment variable is not set",
        troubleshooting=[
            "Set the missing environment variable before starting Orthanc",
            "Example: export VAR_NAME=value",
            "For Docker: use -e VAR_NAME=value or env_file",
        ],
        documentation_url="https://github.com/rhavekost/orthanc-dicomweb-oauth/blob/main/docs/CONFIG.md#environment-variables",
    )

    # Token Acquisition Errors (TOK-xxx)
    TOKEN_ACQUISITION_FAILED = ErrorCodeInfo(
        code="TOK-001",
        category=ErrorCategory.AUTHENTICATION,
        severity=ErrorSeverity.ERROR,
        http_status=401,
        description="Failed to acquire OAuth2 token",
        troubleshooting=[
            "Verify ClientId and ClientSecret are correct",
            "Check that token endpoint URL is accessible",
            "Ensure OAuth2 client has required permissions/grants",
            "Review Orthanc logs for detailed error from provider",
        ],
        documentation_url="https://github.com/rhavekost/orthanc-dicomweb-oauth/blob/main/docs/TROUBLESHOOTING.md#token-acquisition-failures",
    )

    TOKEN_EXPIRED = ErrorCodeInfo(
        code="TOK-002",
        category=ErrorCategory.AUTHENTICATION,
        severity=ErrorSeverity.WARNING,
        http_status=401,
        description="Cached token has expired",
        troubleshooting=[
            "Token will be automatically refreshed on next request",
            "If problem persists, check token endpoint availability",
        ],
        documentation_url="https://github.com/rhavekost/orthanc-dicomweb-oauth/blob/main/docs/TOKEN-MANAGEMENT.md",
    )

    TOKEN_REFRESH_RECOMMENDED = ErrorCodeInfo(
        code="TOK-003",
        category=ErrorCategory.AUTHENTICATION,
        severity=ErrorSeverity.INFO,
        http_status=200,
        description="Token is nearing expiration",
        troubleshooting=[
            "This is informational - no action required",
            "Token will be refreshed automatically",
        ],
        documentation_url="https://github.com/rhavekost/orthanc-dicomweb-oauth/blob/main/docs/TOKEN-MANAGEMENT.md#token-refresh",
    )

    # Network Errors (NET-xxx)
    NETWORK_TIMEOUT = ErrorCodeInfo(
        code="NET-001",
        category=ErrorCategory.NETWORK,
        severity=ErrorSeverity.ERROR,
        http_status=504,
        description="Network timeout connecting to endpoint",
        troubleshooting=[
            "Check network connectivity to the token endpoint",
            "Verify firewall rules allow outbound HTTPS",
            "Increase timeout if endpoint is known to be slow",
            "Check if endpoint is experiencing downtime",
        ],
        documentation_url="https://github.com/rhavekost/orthanc-dicomweb-oauth/blob/main/docs/TROUBLESHOOTING.md#network-errors",
    )

    NETWORK_CONNECTION_ERROR = ErrorCodeInfo(
        code="NET-002",
        category=ErrorCategory.NETWORK,
        severity=ErrorSeverity.ERROR,
        http_status=502,
        description="Cannot establish connection to endpoint",
        troubleshooting=[
            "Verify the endpoint URL is correct and accessible",
            "Check DNS resolution for the endpoint hostname",
            "Ensure no proxy is blocking the connection",
            "Verify SSL/TLS certificates if using HTTPS",
        ],
        documentation_url="https://github.com/rhavekost/orthanc-dicomweb-oauth/blob/main/docs/TROUBLESHOOTING.md#network-errors",
    )

    NETWORK_SSL_ERROR = ErrorCodeInfo(
        code="NET-003",
        category=ErrorCategory.NETWORK,
        severity=ErrorSeverity.ERROR,
        http_status=495,
        description="SSL/TLS certificate verification failed",
        troubleshooting=[
            "Verify the endpoint has a valid SSL certificate",
            "Check certificate expiration date",
            "For self-signed certs, set VerifySSL: false (not recommended for production)",
            "Ensure system CA certificates are up to date",
        ],
        documentation_url="https://github.com/rhavekost/orthanc-dicomweb-oauth/blob/main/docs/CONFIG.md#ssl-verification",
    )

    # Authorization Errors (AUTH-xxx)
    AUTH_INVALID_CREDENTIALS = ErrorCodeInfo(
        code="AUTH-001",
        category=ErrorCategory.AUTHORIZATION,
        severity=ErrorSeverity.ERROR,
        http_status=401,
        description="Invalid client credentials",
        troubleshooting=[
            "Verify ClientId matches the registered OAuth2 client",
            "Verify ClientSecret is correct and not expired",
            "Check if credentials need to be rotated",
            "Ensure OAuth2 client is not disabled",
        ],
        documentation_url="https://github.com/rhavekost/orthanc-dicomweb-oauth/blob/main/docs/OAUTH-PROVIDERS.md",
    )

    AUTH_INSUFFICIENT_SCOPE = ErrorCodeInfo(
        code="AUTH-002",
        category=ErrorCategory.AUTHORIZATION,
        severity=ErrorSeverity.ERROR,
        http_status=403,
        description="Insufficient scope for requested operation",
        troubleshooting=[
            "Add required scope to configuration Scope field",
            "Verify OAuth2 client has permission for requested scope",
            "Check DICOMweb server required scopes",
        ],
        documentation_url="https://github.com/rhavekost/orthanc-dicomweb-oauth/blob/main/docs/CONFIG.md#scopes",
    )

    AUTH_PROVIDER_UNAVAILABLE = ErrorCodeInfo(
        code="AUTH-003",
        category=ErrorCategory.AUTHORIZATION,
        severity=ErrorSeverity.CRITICAL,
        http_status=503,
        description="Authentication provider is unavailable",
        troubleshooting=[
            "Check if OAuth provider is experiencing an outage",
            "Verify network connectivity to provider",
            "Check provider status page if available",
            "Consider implementing fallback authentication",
        ],
        documentation_url="https://github.com/rhavekost/orthanc-dicomweb-oauth/blob/main/docs/TROUBLESHOOTING.md#provider-downtime",
    )

    # Internal Errors (INT-xxx)
    INTERNAL_STATE_ERROR = ErrorCodeInfo(
        code="INT-001",
        category=ErrorCategory.INTERNAL,
        severity=ErrorSeverity.ERROR,
        http_status=500,
        description="Internal state inconsistency detected",
        troubleshooting=[
            "This indicates a bug - please report to maintainers",
            "Restart Orthanc to reset plugin state",
            "Check Orthanc logs for stack trace",
        ],
        documentation_url="https://github.com/rhavekost/orthanc-dicomweb-oauth/issues",
    )

    @property
    def code(self) -> str:
        """Get error code string."""
        return self.value.code

    @property
    def category(self) -> ErrorCategory:
        """Get error category."""
        return self.value.category

    @property
    def severity(self) -> ErrorSeverity:
        """Get error severity."""
        return self.value.severity

    @property
    def http_status(self) -> int:
        """Get HTTP status code."""
        return self.value.http_status

    @property
    def description(self) -> str:
        """Get error description."""
        return self.value.description

    @property
    def troubleshooting(self) -> List[str]:
        """Get troubleshooting steps."""
        return self.value.troubleshooting

    @property
    def documentation_url(self) -> str:
        """Get documentation URL."""
        return self.value.documentation_url


class PluginError(Exception):
    """Base exception with structured error code."""

    def __init__(
        self,
        error_code: ErrorCode,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        severity: Optional[ErrorSeverity] = None,
    ):
        """
        Initialize plugin error.

        Args:
            error_code: Structured error code
            message: Human-readable error message
            details: Additional context (server name, URL, etc.)
            severity: Override default severity
        """
        super().__init__(message)
        self.error_code = error_code
        self.message = message
        self.details = details or {}
        self.severity = severity or error_code.severity
        self.http_status = error_code.http_status
        self.troubleshooting_steps = error_code.troubleshooting
        self.documentation_url = error_code.documentation_url

    def to_dict(self) -> Dict[str, Any]:
        """Serialize error for API responses."""
        return {
            "error_code": self.error_code.code,
            "category": self.error_code.category.value,
            "severity": self.severity.value,
            "message": self.message,
            "details": self.details,
            "troubleshooting": self.troubleshooting_steps,
            "documentation_url": self.documentation_url,
            "http_status": self.http_status,
        }


class ConfigurationError(PluginError):
    """Configuration-related errors."""

    pass


class TokenAcquisitionError(PluginError):
    """Token acquisition errors."""

    pass


class NetworkError(PluginError):
    """Network-related errors."""

    pass


class AuthorizationError(PluginError):
    """Authorization errors."""

    pass


class InternalError(PluginError):
    """Internal plugin errors."""

    pass
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_error_codes.py -v`
Expected: PASS (all tests green)

**Step 5: Commit**

```bash
git add src/error_codes.py tests/test_error_codes.py
git commit -m "feat: add structured error code system with troubleshooting

- Define error categories: CONFIGURATION, AUTHENTICATION, NETWORK, etc.
- Create error codes with metadata: code, severity, HTTP status, troubleshooting
- Implement PluginError base class with structured error information
- Add specific error classes: ConfigurationError, TokenAcquisitionError, etc.
- Include documentation URLs for each error code
- Support error serialization for API responses

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 2: Replace Global State with Singleton Pattern

**Files:**
- Modify: `src/plugin_context.py`
- Modify: `src/dicomweb_oauth_plugin.py`
- Create: `tests/test_singleton_pattern.py`

**Step 1: Write the failing test**

```python
# tests/test_singleton_pattern.py
"""Tests for singleton pattern implementation."""
import threading
import pytest

from src.plugin_context import PluginContext


def test_singleton_instance():
    """Test that PluginContext is a singleton."""
    instance1 = PluginContext.get_instance()
    instance2 = PluginContext.get_instance()

    assert instance1 is instance2


def test_singleton_initialization():
    """Test singleton can be initialized only once."""
    # Reset singleton for test
    PluginContext._instance = None
    PluginContext._initialized = False

    instance1 = PluginContext.get_instance()
    instance1.register_token_manager("test-server", "manager", "http://test.com")

    instance2 = PluginContext.get_instance()
    assert instance2.get_token_manager("test-server") is not None


def test_singleton_thread_safety():
    """Test that singleton is thread-safe."""
    instances = []

    def create_instance():
        instance = PluginContext.get_instance()
        instances.append(id(instance))

    # Reset singleton
    PluginContext._instance = None
    PluginContext._initialized = False

    # Create 10 threads trying to get instance simultaneously
    threads = [threading.Thread(target=create_instance) for _ in range(10)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    # All should have same instance ID
    assert len(set(instances)) == 1


def test_singleton_reset():
    """Test singleton can be reset for testing."""
    instance1 = PluginContext.get_instance()
    instance1.register_token_manager("test1", "manager1", "http://test1.com")

    # Reset
    PluginContext.reset_instance()

    instance2 = PluginContext.get_instance()
    assert instance1 is not instance2
    assert instance2.get_token_manager("test1") is None


def test_no_direct_instantiation():
    """Test that PluginContext cannot be directly instantiated."""
    with pytest.raises(RuntimeError) as exc_info:
        PluginContext()

    assert "Use get_instance()" in str(exc_info.value)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_singleton_pattern.py -v`
Expected: FAIL with "AttributeError: type object 'PluginContext' has no attribute 'get_instance'"

**Step 3: Write minimal implementation**

```python
# src/plugin_context.py
"""Plugin context management using singleton pattern."""
import logging
import threading
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class PluginContext:
    """
    Singleton plugin context for managing token managers.

    Replaces global state pattern with thread-safe singleton.
    """

    _instance: Optional["PluginContext"] = None
    _initialized: bool = False
    _lock: threading.Lock = threading.Lock()

    def __new__(cls) -> "PluginContext":
        """Prevent direct instantiation."""
        raise RuntimeError(
            "PluginContext cannot be instantiated directly. Use get_instance() instead."
        )

    @classmethod
    def get_instance(cls) -> "PluginContext":
        """
        Get singleton instance of PluginContext (thread-safe).

        Returns:
            Singleton PluginContext instance
        """
        if cls._instance is None:
            with cls._lock:
                # Double-checked locking pattern
                if cls._instance is None:
                    # Bypass __new__ for singleton creation
                    instance = object.__new__(cls)
                    instance._initialize()
                    cls._instance = instance
                    cls._initialized = True

        return cls._instance

    def _initialize(self) -> None:
        """Initialize singleton instance."""
        self._token_managers: Dict[str, Any] = {}
        self._server_urls: Dict[str, str] = {}
        self._logger = logging.getLogger(__name__)

    @classmethod
    def reset_instance(cls) -> None:
        """
        Reset singleton instance (for testing only).

        WARNING: This should only be used in tests.
        """
        with cls._lock:
            cls._instance = None
            cls._initialized = False

    def register_token_manager(
        self, server_name: str, manager: Any, url: str
    ) -> None:
        """
        Register a token manager for a DICOMweb server.

        Args:
            server_name: Name of the server
            manager: TokenManager instance
            url: Server URL
        """
        self._token_managers[server_name] = manager
        self._server_urls[server_name] = url
        self._logger.info(f"Registered token manager for server: {server_name}")

    def get_token_manager(self, server_name: str) -> Optional[Any]:
        """
        Get token manager for a server.

        Args:
            server_name: Name of the server

        Returns:
            TokenManager instance or None if not found
        """
        return self._token_managers.get(server_name)

    def get_server_url(self, server_name: str) -> Optional[str]:
        """
        Get URL for a server.

        Args:
            server_name: Name of the server

        Returns:
            Server URL or None if not found
        """
        return self._server_urls.get(server_name)

    def find_server_for_url(self, url: str) -> Optional[str]:
        """
        Find server name for a given URL.

        Args:
            url: URL to match

        Returns:
            Server name or None if no match
        """
        for server_name, server_url in self._server_urls.items():
            if url.startswith(server_url):
                return server_name
        return None

    def get_all_servers(self) -> Dict[str, str]:
        """
        Get all registered servers.

        Returns:
            Dictionary mapping server names to URLs
        """
        return self._server_urls.copy()
```

**Step 4: Update plugin to use singleton**

```python
# Modify src/dicomweb_oauth_plugin.py

# Remove global variable:
# _plugin_context: Optional[PluginContext] = None  # DELETE THIS

def initialize_plugin(
    orthanc_module: Any = None, context: Optional[PluginContext] = None
) -> None:
    """
    Initialize the DICOMweb OAuth plugin.

    Args:
        orthanc_module: Orthanc module (for testing, defaults to global orthanc)
        context: Plugin context (for testing, uses singleton if None)
    """
    # Remove: global _plugin_context

    if orthanc_module is None:
        orthanc_module = orthanc

    # Use singleton pattern instead of global
    if context is None:
        context = PluginContext.get_instance()

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
                server_name=server_name, manager=manager, url=server_config["Url"]
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
    """Get the plugin context (singleton)."""
    return PluginContext.get_instance()


# Update all references from _plugin_context to PluginContext.get_instance()
```

**Step 5: Run tests to verify**

Run: `pytest tests/test_singleton_pattern.py tests/test_plugin_integration.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add src/plugin_context.py src/dicomweb_oauth_plugin.py tests/test_singleton_pattern.py
git commit -m "refactor: replace global state with singleton pattern

- Implement thread-safe singleton pattern for PluginContext
- Add double-checked locking for thread safety
- Remove global _plugin_context variable (anti-pattern)
- Add reset_instance() for testing
- Prevent direct instantiation with RuntimeError
- Update all references to use get_instance()

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 3: Implement Circuit Breaker Pattern

**Files:**
- Create: `src/resilience/circuit_breaker.py`
- Create: `src/resilience/__init__.py`
- Create: `tests/test_circuit_breaker.py`

**Step 1: Write the failing test**

```python
# tests/test_circuit_breaker.py
"""Tests for circuit breaker pattern."""
import time
import pytest

from src.resilience.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerState,
    CircuitBreakerError,
)


def test_circuit_breaker_success():
    """Test circuit breaker in closed state with successful calls."""
    cb = CircuitBreaker(failure_threshold=3, timeout=1)

    def successful_operation():
        return "success"

    result = cb.call(successful_operation)
    assert result == "success"
    assert cb.state == CircuitBreakerState.CLOSED
    assert cb.failure_count == 0


def test_circuit_breaker_opens_on_failures():
    """Test circuit breaker opens after failure threshold."""
    cb = CircuitBreaker(failure_threshold=3, timeout=1)

    def failing_operation():
        raise Exception("Service unavailable")

    # First 2 failures should keep circuit closed
    for i in range(2):
        with pytest.raises(Exception):
            cb.call(failing_operation)
        assert cb.state == CircuitBreakerState.CLOSED

    # 3rd failure should open circuit
    with pytest.raises(Exception):
        cb.call(failing_operation)
    assert cb.state == CircuitBreakerState.OPEN
    assert cb.failure_count == 3


def test_circuit_breaker_rejects_calls_when_open():
    """Test circuit breaker rejects calls in open state."""
    cb = CircuitBreaker(failure_threshold=2, timeout=1)

    def failing_operation():
        raise Exception("Service unavailable")

    # Trigger failures to open circuit
    for _ in range(2):
        with pytest.raises(Exception):
            cb.call(failing_operation)

    assert cb.state == CircuitBreakerState.OPEN

    # Next call should be rejected immediately
    with pytest.raises(CircuitBreakerError) as exc_info:
        cb.call(failing_operation)

    assert "Circuit breaker is OPEN" in str(exc_info.value)


def test_circuit_breaker_half_open_after_timeout():
    """Test circuit breaker transitions to half-open after timeout."""
    cb = CircuitBreaker(failure_threshold=2, timeout=0.1)

    def failing_operation():
        raise Exception("Service unavailable")

    # Open the circuit
    for _ in range(2):
        with pytest.raises(Exception):
            cb.call(failing_operation)

    assert cb.state == CircuitBreakerState.OPEN

    # Wait for timeout
    time.sleep(0.15)

    # Next call should transition to half-open
    def successful_operation():
        return "success"

    result = cb.call(successful_operation)
    assert result == "success"
    assert cb.state == CircuitBreakerState.CLOSED


def test_circuit_breaker_resets_on_success():
    """Test circuit breaker resets failure count on success."""
    cb = CircuitBreaker(failure_threshold=3, timeout=1)

    def failing_operation():
        raise Exception("Service unavailable")

    def successful_operation():
        return "success"

    # 2 failures
    for _ in range(2):
        with pytest.raises(Exception):
            cb.call(failing_operation)

    assert cb.failure_count == 2

    # Success should reset counter
    cb.call(successful_operation)
    assert cb.failure_count == 0
    assert cb.state == CircuitBreakerState.CLOSED


def test_circuit_breaker_with_custom_exception_filter():
    """Test circuit breaker with exception filter."""

    class NetworkError(Exception):
        pass

    class ValidationError(Exception):
        pass

    cb = CircuitBreaker(
        failure_threshold=2,
        timeout=1,
        exception_filter=lambda e: isinstance(e, NetworkError),
    )

    def operation_with_network_error():
        raise NetworkError("Connection failed")

    def operation_with_validation_error():
        raise ValidationError("Invalid input")

    # ValidationError shouldn't count toward failures
    with pytest.raises(ValidationError):
        cb.call(operation_with_validation_error)

    assert cb.failure_count == 0

    # NetworkError should count
    with pytest.raises(NetworkError):
        cb.call(operation_with_network_error)

    assert cb.failure_count == 1


def test_circuit_breaker_metrics():
    """Test circuit breaker exposes metrics."""
    cb = CircuitBreaker(failure_threshold=3, timeout=1)

    def operation():
        return "success"

    # Execute some calls
    for _ in range(5):
        cb.call(operation)

    metrics = cb.get_metrics()

    assert metrics["state"] == "CLOSED"
    assert metrics["failure_count"] == 0
    assert metrics["total_calls"] == 5
    assert metrics["success_count"] == 5
    assert metrics["failure_threshold"] == 3
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_circuit_breaker.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'src.resilience'"

**Step 3: Write minimal implementation**

```python
# src/resilience/__init__.py
"""Resilience patterns for fault tolerance."""
from src.resilience.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerState,
    CircuitBreakerError,
)

__all__ = ["CircuitBreaker", "CircuitBreakerState", "CircuitBreakerError"]
```

```python
# src/resilience/circuit_breaker.py
"""Circuit breaker pattern implementation."""
import logging
import threading
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


class CircuitBreakerState(str, Enum):
    """Circuit breaker states."""

    CLOSED = "CLOSED"  # Normal operation
    OPEN = "OPEN"  # Failing, reject calls
    HALF_OPEN = "HALF_OPEN"  # Testing recovery


class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open."""

    pass


@dataclass
class CircuitBreakerMetrics:
    """Metrics for circuit breaker."""

    total_calls: int = 0
    success_count: int = 0
    failure_count: int = 0
    rejected_count: int = 0


class CircuitBreaker:
    """
    Circuit breaker pattern for fault tolerance.

    Prevents cascading failures by opening circuit after threshold failures.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: float = 60.0,
        exception_filter: Optional[Callable[[Exception], bool]] = None,
    ):
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            timeout: Seconds before attempting to close circuit (half-open)
            exception_filter: Optional function to filter which exceptions count as failures
        """
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.exception_filter = exception_filter or (lambda e: True)

        self._state = CircuitBreakerState.CLOSED
        self._failure_count = 0
        self._last_failure_time: Optional[float] = None
        self._lock = threading.Lock()

        # Metrics
        self._metrics = CircuitBreakerMetrics()

    @property
    def state(self) -> CircuitBreakerState:
        """Get current circuit breaker state."""
        with self._lock:
            return self._state

    @property
    def failure_count(self) -> int:
        """Get current failure count."""
        with self._lock:
            return self._failure_count

    def call(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """
        Execute function with circuit breaker protection.

        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result

        Raises:
            CircuitBreakerError: If circuit is open
            Exception: Original exception from func
        """
        with self._lock:
            self._metrics.total_calls += 1

            # Check if we should transition from OPEN to HALF_OPEN
            if self._state == CircuitBreakerState.OPEN:
                if self._should_attempt_reset():
                    self._state = CircuitBreakerState.HALF_OPEN
                    logger.info("Circuit breaker entering HALF_OPEN state")
                else:
                    self._metrics.rejected_count += 1
                    raise CircuitBreakerError(
                        f"Circuit breaker is OPEN (failures: {self._failure_count})"
                    )

        # Execute the function
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            if self.exception_filter(e):
                self._on_failure()
            raise

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if self._last_failure_time is None:
            return True
        return time.time() - self._last_failure_time >= self.timeout

    def _on_success(self) -> None:
        """Handle successful call."""
        with self._lock:
            self._metrics.success_count += 1
            self._failure_count = 0

            if self._state == CircuitBreakerState.HALF_OPEN:
                self._state = CircuitBreakerState.CLOSED
                logger.info("Circuit breaker CLOSED after successful call")

    def _on_failure(self) -> None:
        """Handle failed call."""
        with self._lock:
            self._metrics.failure_count += 1
            self._failure_count += 1
            self._last_failure_time = time.time()

            if self._failure_count >= self.failure_threshold:
                if self._state != CircuitBreakerState.OPEN:
                    self._state = CircuitBreakerState.OPEN
                    logger.warning(
                        f"Circuit breaker OPENED after {self._failure_count} failures"
                    )

    def reset(self) -> None:
        """Manually reset circuit breaker to closed state."""
        with self._lock:
            self._state = CircuitBreakerState.CLOSED
            self._failure_count = 0
            self._last_failure_time = None
            logger.info("Circuit breaker manually reset to CLOSED")

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get circuit breaker metrics.

        Returns:
            Dictionary with metrics
        """
        with self._lock:
            return {
                "state": self._state.value,
                "failure_count": self._failure_count,
                "failure_threshold": self.failure_threshold,
                "total_calls": self._metrics.total_calls,
                "success_count": self._metrics.success_count,
                "rejected_count": self._metrics.rejected_count,
                "timeout_seconds": self.timeout,
            }
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_circuit_breaker.py -v`
Expected: PASS (all tests green)

**Step 5: Commit**

```bash
git add src/resilience/ tests/test_circuit_breaker.py
git commit -m "feat: implement circuit breaker pattern for resilience

- Create CircuitBreaker class with CLOSED/OPEN/HALF_OPEN states
- Implement failure threshold with automatic circuit opening
- Add timeout-based recovery to half-open state
- Support custom exception filtering
- Add thread-safe state management
- Expose metrics for monitoring (calls, failures, state)
- Prevent cascading failures with fast-fail when open

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 4: Implement Configurable Retry Strategy

**Files:**
- Create: `src/resilience/retry_strategy.py`
- Modify: `src/resilience/__init__.py`
- Create: `tests/test_retry_strategy.py`

**Step 1: Write the failing test**

```python
# tests/test_retry_strategy.py
"""Tests for retry strategy patterns."""
import time
import pytest

from src.resilience.retry_strategy import (
    RetryStrategy,
    ExponentialBackoff,
    LinearBackoff,
    FixedBackoff,
    RetryConfig,
    RetryExhaustedError,
)


def test_fixed_backoff_delays():
    """Test fixed backoff calculates constant delays."""
    strategy = FixedBackoff(delay=1.0)

    assert strategy.get_delay(0) == 1.0
    assert strategy.get_delay(1) == 1.0
    assert strategy.get_delay(5) == 1.0


def test_linear_backoff_delays():
    """Test linear backoff increases linearly."""
    strategy = LinearBackoff(initial_delay=1.0, increment=0.5)

    assert strategy.get_delay(0) == 1.0
    assert strategy.get_delay(1) == 1.5
    assert strategy.get_delay(2) == 2.0
    assert strategy.get_delay(3) == 2.5


def test_exponential_backoff_delays():
    """Test exponential backoff doubles delay."""
    strategy = ExponentialBackoff(initial_delay=1.0, multiplier=2.0)

    assert strategy.get_delay(0) == 1.0
    assert strategy.get_delay(1) == 2.0
    assert strategy.get_delay(2) == 4.0
    assert strategy.get_delay(3) == 8.0


def test_exponential_backoff_with_max_delay():
    """Test exponential backoff respects max delay."""
    strategy = ExponentialBackoff(initial_delay=1.0, multiplier=2.0, max_delay=5.0)

    assert strategy.get_delay(0) == 1.0
    assert strategy.get_delay(1) == 2.0
    assert strategy.get_delay(2) == 4.0
    assert strategy.get_delay(3) == 5.0  # Capped
    assert strategy.get_delay(4) == 5.0  # Still capped


def test_retry_config_max_attempts():
    """Test retry config respects max attempts."""
    config = RetryConfig(max_attempts=3, strategy=FixedBackoff(delay=0.01))

    call_count = 0

    def failing_operation():
        nonlocal call_count
        call_count += 1
        raise Exception("Always fails")

    with pytest.raises(RetryExhaustedError) as exc_info:
        config.execute(failing_operation)

    assert call_count == 3
    assert "after 3 attempts" in str(exc_info.value)


def test_retry_config_success_on_retry():
    """Test retry config succeeds after failures."""
    config = RetryConfig(max_attempts=3, strategy=FixedBackoff(delay=0.01))

    call_count = 0

    def operation_succeeds_on_second_try():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise Exception("Not yet")
        return "success"

    result = config.execute(operation_succeeds_on_second_try)

    assert result == "success"
    assert call_count == 2


def test_retry_config_with_exception_filter():
    """Test retry only on specific exceptions."""

    class RetryableError(Exception):
        pass

    class NonRetryableError(Exception):
        pass

    config = RetryConfig(
        max_attempts=3,
        strategy=FixedBackoff(delay=0.01),
        should_retry=lambda e: isinstance(e, RetryableError),
    )

    # Non-retryable exception should fail immediately
    with pytest.raises(NonRetryableError):
        config.execute(lambda: (_ for _ in ()).throw(NonRetryableError("Immediate")))

    # Retryable exception should retry
    call_count = 0

    def retryable_operation():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise RetryableError("Retry me")
        return "success"

    result = config.execute(retryable_operation)
    assert result == "success"
    assert call_count == 2


def test_retry_config_timing():
    """Test retry config respects backoff timing."""
    config = RetryConfig(max_attempts=3, strategy=FixedBackoff(delay=0.1))

    call_count = 0
    start_time = time.time()

    def failing_operation():
        nonlocal call_count
        call_count += 1
        raise Exception("Always fails")

    with pytest.raises(RetryExhaustedError):
        config.execute(failing_operation)

    elapsed = time.time() - start_time

    # Should have 2 delays (between 3 attempts) of 0.1s each
    assert elapsed >= 0.2
    assert call_count == 3


def test_retry_config_callback():
    """Test retry config calls callback on each attempt."""
    attempts_log = []

    def on_retry(attempt: int, exception: Exception):
        attempts_log.append((attempt, str(exception)))

    config = RetryConfig(
        max_attempts=3, strategy=FixedBackoff(delay=0.01), on_retry=on_retry
    )

    def failing_operation():
        raise ValueError("Test error")

    with pytest.raises(RetryExhaustedError):
        config.execute(failing_operation)

    assert len(attempts_log) == 2  # Callbacks before 2nd and 3rd attempts
    assert attempts_log[0][0] == 1
    assert "Test error" in attempts_log[0][1]
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_retry_strategy.py -v`
Expected: FAIL with "ImportError: cannot import name 'RetryStrategy'"

**Step 3: Write minimal implementation**

```python
# src/resilience/retry_strategy.py
"""Configurable retry strategies with various backoff algorithms."""
import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class RetryExhaustedError(Exception):
    """Raised when all retry attempts are exhausted."""

    pass


class RetryStrategy(ABC):
    """Abstract base class for retry strategies."""

    @abstractmethod
    def get_delay(self, attempt: int) -> float:
        """
        Calculate delay for given attempt number.

        Args:
            attempt: Current attempt number (0-indexed)

        Returns:
            Delay in seconds before next retry
        """
        pass


class FixedBackoff(RetryStrategy):
    """Fixed delay between retries."""

    def __init__(self, delay: float):
        """
        Initialize fixed backoff.

        Args:
            delay: Fixed delay in seconds
        """
        self.delay = delay

    def get_delay(self, attempt: int) -> float:
        """Return fixed delay regardless of attempt."""
        return self.delay


class LinearBackoff(RetryStrategy):
    """Linear increase in delay between retries."""

    def __init__(self, initial_delay: float, increment: float):
        """
        Initialize linear backoff.

        Args:
            initial_delay: Initial delay in seconds
            increment: Amount to increase delay each attempt
        """
        self.initial_delay = initial_delay
        self.increment = increment

    def get_delay(self, attempt: int) -> float:
        """Return linearly increasing delay."""
        return self.initial_delay + (attempt * self.increment)


class ExponentialBackoff(RetryStrategy):
    """Exponential increase in delay between retries."""

    def __init__(
        self, initial_delay: float, multiplier: float = 2.0, max_delay: Optional[float] = None
    ):
        """
        Initialize exponential backoff.

        Args:
            initial_delay: Initial delay in seconds
            multiplier: Factor to multiply delay each attempt
            max_delay: Maximum delay cap (optional)
        """
        self.initial_delay = initial_delay
        self.multiplier = multiplier
        self.max_delay = max_delay

    def get_delay(self, attempt: int) -> float:
        """Return exponentially increasing delay."""
        delay = self.initial_delay * (self.multiplier ** attempt)

        if self.max_delay is not None:
            delay = min(delay, self.max_delay)

        return delay


class RetryConfig:
    """Configuration for retry behavior with strategy pattern."""

    def __init__(
        self,
        max_attempts: int,
        strategy: RetryStrategy,
        should_retry: Optional[Callable[[Exception], bool]] = None,
        on_retry: Optional[Callable[[int, Exception], None]] = None,
    ):
        """
        Initialize retry configuration.

        Args:
            max_attempts: Maximum number of attempts
            strategy: Retry strategy for calculating delays
            should_retry: Optional function to determine if exception should trigger retry
            on_retry: Optional callback before each retry
        """
        self.max_attempts = max_attempts
        self.strategy = strategy
        self.should_retry = should_retry or (lambda e: True)
        self.on_retry = on_retry

    def execute(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """
        Execute function with retry logic.

        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result

        Raises:
            RetryExhaustedError: If all attempts fail
            Exception: If exception is not retryable
        """
        last_exception: Optional[Exception] = None

        for attempt in range(self.max_attempts):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e

                # Check if we should retry this exception
                if not self.should_retry(e):
                    raise

                # Check if we have attempts remaining
                if attempt >= self.max_attempts - 1:
                    break

                # Call retry callback if provided
                if self.on_retry:
                    self.on_retry(attempt, e)

                # Calculate and apply delay
                delay = self.strategy.get_delay(attempt)
                logger.debug(
                    f"Retry attempt {attempt + 1}/{self.max_attempts} "
                    f"after {delay}s delay"
                )
                time.sleep(delay)

        # All attempts exhausted
        raise RetryExhaustedError(
            f"Operation failed after {self.max_attempts} attempts: {last_exception}"
        ) from last_exception
```

**Step 4: Update __init__.py**

```python
# src/resilience/__init__.py
"""Resilience patterns for fault tolerance."""
from src.resilience.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerState,
    CircuitBreakerError,
)
from src.resilience.retry_strategy import (
    RetryStrategy,
    RetryConfig,
    ExponentialBackoff,
    LinearBackoff,
    FixedBackoff,
    RetryExhaustedError,
)

__all__ = [
    "CircuitBreaker",
    "CircuitBreakerState",
    "CircuitBreakerError",
    "RetryStrategy",
    "RetryConfig",
    "ExponentialBackoff",
    "LinearBackoff",
    "FixedBackoff",
    "RetryExhaustedError",
]
```

**Step 5: Run test to verify it passes**

Run: `pytest tests/test_retry_strategy.py -v`
Expected: PASS (all tests green)

**Step 6: Commit**

```bash
git add src/resilience/retry_strategy.py src/resilience/__init__.py tests/test_retry_strategy.py
git commit -m "feat: implement configurable retry strategies

- Create RetryStrategy abstract base class
- Implement FixedBackoff (constant delay)
- Implement LinearBackoff (linear increase)
- Implement ExponentialBackoff (exponential with optional max)
- Add RetryConfig for composable retry behavior
- Support exception filtering (should_retry callback)
- Add retry callbacks for monitoring (on_retry)
- Raise RetryExhaustedError when all attempts fail

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 5: Integrate Circuit Breaker with Token Manager

**Files:**
- Modify: `src/token_manager.py`
- Modify: `src/config_schema.py`
- Create: `tests/test_token_manager_resilience.py`

**Step 1: Write the failing test**

```python
# tests/test_token_manager_resilience.py
"""Tests for token manager resilience features."""
import pytest
import time

from src.token_manager import TokenManager
from src.resilience.circuit_breaker import CircuitBreakerError, CircuitBreakerState
from src.oauth_providers.base import TokenAcquisitionError


def test_token_manager_circuit_breaker_opens_on_failures(mocker):
    """Test circuit breaker opens after threshold failures."""
    config = {
        "TokenEndpoint": "https://test.com/token",
        "ClientId": "test-id",
        "ClientSecret": "test-secret",
        "ResilienceConfig": {
            "CircuitBreakerEnabled": True,
            "CircuitBreakerFailureThreshold": 2,
            "CircuitBreakerTimeout": 1,
        },
    }

    manager = TokenManager("test-server", config)

    # Mock provider to always fail
    mock_provider = mocker.patch.object(manager.provider, "acquire_token")
    mock_provider.side_effect = Exception("Service unavailable")

    # First 2 failures should attempt call
    for _ in range(2):
        with pytest.raises(TokenAcquisitionError):
            manager.get_token()

    # Circuit should now be open
    assert manager._circuit_breaker.state == CircuitBreakerState.OPEN

    # Next call should fail fast
    with pytest.raises(CircuitBreakerError):
        manager.get_token()


def test_token_manager_configurable_retry_strategy(mocker):
    """Test token manager uses configured retry strategy."""
    config = {
        "TokenEndpoint": "https://test.com/token",
        "ClientId": "test-id",
        "ClientSecret": "test-secret",
        "ResilienceConfig": {
            "RetryMaxAttempts": 3,
            "RetryStrategy": "exponential",
            "RetryInitialDelay": 0.1,
            "RetryMultiplier": 2.0,
        },
    }

    manager = TokenManager("test-server", config)

    call_count = 0

    def failing_then_success():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise Exception("Not yet")
        return {"access_token": "token123", "expires_in": 3600}

    mock_provider = mocker.patch.object(manager.provider, "acquire_token")
    mock_provider.side_effect = failing_then_success

    # Should succeed after retries
    token = manager.get_token()
    assert token == "token123"
    assert call_count == 3


def test_token_manager_circuit_breaker_disabled_by_default(mocker):
    """Test circuit breaker is disabled by default for backward compatibility."""
    config = {
        "TokenEndpoint": "https://test.com/token",
        "ClientId": "test-id",
        "ClientSecret": "test-secret",
    }

    manager = TokenManager("test-server", config)

    # Circuit breaker should be None when disabled
    assert manager._circuit_breaker is None


def test_token_manager_retry_disabled_by_default(mocker):
    """Test retry is disabled by default for backward compatibility."""
    config = {
        "TokenEndpoint": "https://test.com/token",
        "ClientId": "test-id",
        "ClientSecret": "test-secret",
    }

    manager = TokenManager("test-server", config)

    # Retry config should be None when disabled
    assert manager._retry_config is None
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_token_manager_resilience.py -v`
Expected: FAIL with "AttributeError: 'TokenManager' object has no attribute '_circuit_breaker'"

**Step 3: Update config schema**

```python
# Modify src/config_schema.py - add to server schema

"ResilienceConfig": {
    "type": "object",
    "properties": {
        "CircuitBreakerEnabled": {"type": "boolean"},
        "CircuitBreakerFailureThreshold": {"type": "integer", "minimum": 1},
        "CircuitBreakerTimeout": {"type": "number", "minimum": 0},
        "RetryMaxAttempts": {"type": "integer", "minimum": 1},
        "RetryStrategy": {"type": "string", "enum": ["fixed", "linear", "exponential"]},
        "RetryInitialDelay": {"type": "number", "minimum": 0},
        "RetryMultiplier": {"type": "number", "minimum": 1},
        "RetryMaxDelay": {"type": "number", "minimum": 0},
    },
    "additionalProperties": False,
}
```

**Step 4: Update token manager**

```python
# Modify src/token_manager.py

from src.resilience import (
    CircuitBreaker,
    RetryConfig,
    ExponentialBackoff,
    LinearBackoff,
    FixedBackoff,
)

class TokenManager:
    def __init__(self, server_name: str, config: Dict[str, Any]):
        # ... existing initialization ...

        # Initialize resilience features
        self._circuit_breaker = self._create_circuit_breaker(config)
        self._retry_config = self._create_retry_config(config)

    def _create_circuit_breaker(
        self, config: Dict[str, Any]
    ) -> Optional[CircuitBreaker]:
        """Create circuit breaker from config."""
        resilience_config = config.get("ResilienceConfig", {})

        if not resilience_config.get("CircuitBreakerEnabled", False):
            return None

        return CircuitBreaker(
            failure_threshold=resilience_config.get(
                "CircuitBreakerFailureThreshold", 5
            ),
            timeout=resilience_config.get("CircuitBreakerTimeout", 60.0),
            exception_filter=lambda e: isinstance(
                e, (requests.Timeout, requests.ConnectionError, TokenAcquisitionError)
            ),
        )

    def _create_retry_config(self, config: Dict[str, Any]) -> Optional[RetryConfig]:
        """Create retry config from config."""
        resilience_config = config.get("ResilienceConfig", {})

        max_attempts = resilience_config.get("RetryMaxAttempts")
        if max_attempts is None:
            return None

        # Create strategy based on config
        strategy_type = resilience_config.get("RetryStrategy", "exponential")
        initial_delay = resilience_config.get("RetryInitialDelay", 1.0)

        if strategy_type == "fixed":
            strategy = FixedBackoff(delay=initial_delay)
        elif strategy_type == "linear":
            increment = resilience_config.get("RetryIncrement", 1.0)
            strategy = LinearBackoff(initial_delay=initial_delay, increment=increment)
        else:  # exponential
            multiplier = resilience_config.get("RetryMultiplier", 2.0)
            max_delay = resilience_config.get("RetryMaxDelay")
            strategy = ExponentialBackoff(
                initial_delay=initial_delay,
                multiplier=multiplier,
                max_delay=max_delay,
            )

        return RetryConfig(
            max_attempts=max_attempts,
            strategy=strategy,
            should_retry=lambda e: isinstance(
                e, (requests.Timeout, requests.ConnectionError)
            ),
            on_retry=lambda attempt, exc: structured_logger.warning(
                "Token acquisition retry",
                server=self.server_name,
                attempt=attempt + 1,
                max_attempts=max_attempts,
                error=str(exc),
            ),
        )

    def _acquire_token(self) -> str:
        """Acquire token with resilience patterns."""

        def acquire_operation():
            # Existing token acquisition logic
            return self._acquire_token_with_retry()

        # Apply circuit breaker if enabled
        if self._circuit_breaker:
            result = self._circuit_breaker.call(acquire_operation)
        else:
            result = acquire_operation()

        # ... rest of existing logic ...
```

**Step 5: Run test to verify it passes**

Run: `pytest tests/test_token_manager_resilience.py -v`
Expected: PASS (all tests green)

**Step 6: Commit**

```bash
git add src/token_manager.py src/config_schema.py tests/test_token_manager_resilience.py
git commit -m "feat: integrate circuit breaker and retry with token manager

- Add ResilienceConfig section to config schema
- Support CircuitBreakerEnabled, failure threshold, timeout
- Support RetryMaxAttempts, strategy (fixed/linear/exponential)
- Create circuit breaker from config in TokenManager
- Create retry config from config in TokenManager
- Apply circuit breaker to token acquisition
- Both features disabled by default for backward compatibility
- Log retry attempts with structured logging

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 6: Add Prometheus Metrics Support

**Files:**
- Create: `src/metrics/__init__.py`
- Create: `src/metrics/prometheus.py`
- Create: `tests/test_prometheus_metrics.py`
- Modify: `requirements.txt`

**Step 1: Update requirements**

```bash
echo "prometheus-client==0.19.0" >> requirements.txt
```

**Step 2: Write the failing test**

```python
# tests/test_prometheus_metrics.py
"""Tests for Prometheus metrics collection."""
import pytest
from prometheus_client import REGISTRY

from src.metrics.prometheus import (
    MetricsCollector,
    get_metrics_text,
    reset_metrics,
)


@pytest.fixture(autouse=True)
def reset_prometheus_metrics():
    """Reset metrics before each test."""
    reset_metrics()
    yield
    reset_metrics()


def test_metrics_collector_singleton():
    """Test metrics collector is a singleton."""
    collector1 = MetricsCollector.get_instance()
    collector2 = MetricsCollector.get_instance()

    assert collector1 is collector2


def test_token_acquisition_metrics():
    """Test token acquisition metrics."""
    collector = MetricsCollector.get_instance()

    # Record successful acquisition
    collector.record_token_acquisition(
        server="test-server", success=True, duration=0.5
    )

    # Record failed acquisition
    collector.record_token_acquisition(
        server="test-server", success=False, duration=0.3
    )

    metrics_text = get_metrics_text()

    # Check counter metrics
    assert 'dicomweb_oauth_token_acquisitions_total{server="test-server",status="success"} 1.0' in metrics_text
    assert 'dicomweb_oauth_token_acquisitions_total{server="test-server",status="failure"} 1.0' in metrics_text

    # Check histogram metrics (duration)
    assert "dicomweb_oauth_token_acquisition_duration_seconds" in metrics_text


def test_token_cache_metrics():
    """Test token cache hit/miss metrics."""
    collector = MetricsCollector.get_instance()

    # Record cache hits and misses
    collector.record_cache_hit("test-server")
    collector.record_cache_hit("test-server")
    collector.record_cache_miss("test-server")

    metrics_text = get_metrics_text()

    assert 'dicomweb_oauth_cache_hits_total{server="test-server"} 2.0' in metrics_text
    assert 'dicomweb_oauth_cache_misses_total{server="test-server"} 1.0' in metrics_text


def test_circuit_breaker_metrics():
    """Test circuit breaker state metrics."""
    collector = MetricsCollector.get_instance()

    # Record circuit breaker state changes
    collector.set_circuit_breaker_state("test-server", "CLOSED")
    collector.record_circuit_breaker_rejection("test-server")

    metrics_text = get_metrics_text()

    assert 'dicomweb_oauth_circuit_breaker_state{server="test-server"} 0.0' in metrics_text  # CLOSED=0
    assert 'dicomweb_oauth_circuit_breaker_rejections_total{server="test-server"} 1.0' in metrics_text


def test_retry_metrics():
    """Test retry attempt metrics."""
    collector = MetricsCollector.get_instance()

    # Record retry attempts
    collector.record_retry_attempt("test-server", attempt=1, max_attempts=3)
    collector.record_retry_attempt("test-server", attempt=2, max_attempts=3)

    metrics_text = get_metrics_text()

    assert 'dicomweb_oauth_retry_attempts_total{server="test-server"} 2.0' in metrics_text


def test_http_request_metrics():
    """Test HTTP request metrics."""
    collector = MetricsCollector.get_instance()

    # Record HTTP requests
    collector.record_http_request(
        method="POST", endpoint="/token", status_code=200, duration=0.15
    )
    collector.record_http_request(
        method="POST", endpoint="/token", status_code=500, duration=0.05
    )

    metrics_text = get_metrics_text()

    assert 'dicomweb_oauth_http_requests_total{endpoint="/token",method="POST",status="200"} 1.0' in metrics_text
    assert 'dicomweb_oauth_http_requests_total{endpoint="/token",method="POST",status="500"} 1.0' in metrics_text
    assert "dicomweb_oauth_http_request_duration_seconds" in metrics_text


def test_error_code_metrics():
    """Test error code metrics."""
    collector = MetricsCollector.get_instance()

    # Record errors
    collector.record_error("test-server", error_code="TOK-001", category="AUTHENTICATION")
    collector.record_error("test-server", error_code="NET-001", category="NETWORK")

    metrics_text = get_metrics_text()

    assert 'dicomweb_oauth_errors_total{category="AUTHENTICATION",error_code="TOK-001",server="test-server"} 1.0' in metrics_text
    assert 'dicomweb_oauth_errors_total{category="NETWORK",error_code="NET-001",server="test-server"} 1.0' in metrics_text
```

**Step 3: Run test to verify it fails**

Run: `pytest tests/test_prometheus_metrics.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'src.metrics'"

**Step 4: Write minimal implementation**

```python
# src/metrics/__init__.py
"""Metrics collection for monitoring."""
from src.metrics.prometheus import MetricsCollector, get_metrics_text, reset_metrics

__all__ = ["MetricsCollector", "get_metrics_text", "reset_metrics"]
```

```python
# src/metrics/prometheus.py
"""Prometheus metrics collection."""
import threading
from typing import Optional

from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    REGISTRY,
    generate_latest,
    CollectorRegistry,
)


# Create separate registry for testing
_custom_registry: Optional[CollectorRegistry] = None


def _get_registry() -> CollectorRegistry:
    """Get the registry (custom for tests, default otherwise)."""
    return _custom_registry if _custom_registry is not None else REGISTRY


class MetricsCollector:
    """
    Singleton metrics collector for Prometheus.

    Collects metrics for token acquisition, caching, circuit breaker, retries, etc.
    """

    _instance: Optional["MetricsCollector"] = None
    _lock: threading.Lock = threading.Lock()

    def __new__(cls) -> "MetricsCollector":
        """Prevent direct instantiation."""
        raise RuntimeError("Use get_instance() instead")

    @classmethod
    def get_instance(cls) -> "MetricsCollector":
        """Get singleton instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    instance = object.__new__(cls)
                    instance._initialize()
                    cls._instance = instance
        return cls._instance

    def _initialize(self) -> None:
        """Initialize metrics."""
        registry = _get_registry()

        # Token acquisition metrics
        self.token_acquisitions = Counter(
            "dicomweb_oauth_token_acquisitions_total",
            "Total token acquisition attempts",
            ["server", "status"],
            registry=registry,
        )

        self.token_acquisition_duration = Histogram(
            "dicomweb_oauth_token_acquisition_duration_seconds",
            "Token acquisition duration",
            ["server"],
            registry=registry,
        )

        # Cache metrics
        self.cache_hits = Counter(
            "dicomweb_oauth_cache_hits_total",
            "Total cache hits",
            ["server"],
            registry=registry,
        )

        self.cache_misses = Counter(
            "dicomweb_oauth_cache_misses_total",
            "Total cache misses",
            ["server"],
            registry=registry,
        )

        # Circuit breaker metrics
        self.circuit_breaker_state = Gauge(
            "dicomweb_oauth_circuit_breaker_state",
            "Circuit breaker state (0=CLOSED, 1=OPEN, 2=HALF_OPEN)",
            ["server"],
            registry=registry,
        )

        self.circuit_breaker_rejections = Counter(
            "dicomweb_oauth_circuit_breaker_rejections_total",
            "Total circuit breaker rejections",
            ["server"],
            registry=registry,
        )

        # Retry metrics
        self.retry_attempts = Counter(
            "dicomweb_oauth_retry_attempts_total",
            "Total retry attempts",
            ["server"],
            registry=registry,
        )

        # HTTP request metrics
        self.http_requests = Counter(
            "dicomweb_oauth_http_requests_total",
            "Total HTTP requests",
            ["method", "endpoint", "status"],
            registry=registry,
        )

        self.http_request_duration = Histogram(
            "dicomweb_oauth_http_request_duration_seconds",
            "HTTP request duration",
            ["method", "endpoint"],
            registry=registry,
        )

        # Error metrics
        self.errors = Counter(
            "dicomweb_oauth_errors_total",
            "Total errors by code and category",
            ["server", "error_code", "category"],
            registry=registry,
        )

    def record_token_acquisition(
        self, server: str, success: bool, duration: float
    ) -> None:
        """Record token acquisition attempt."""
        status = "success" if success else "failure"
        self.token_acquisitions.labels(server=server, status=status).inc()
        self.token_acquisition_duration.labels(server=server).observe(duration)

    def record_cache_hit(self, server: str) -> None:
        """Record cache hit."""
        self.cache_hits.labels(server=server).inc()

    def record_cache_miss(self, server: str) -> None:
        """Record cache miss."""
        self.cache_misses.labels(server=server).inc()

    def set_circuit_breaker_state(self, server: str, state: str) -> None:
        """Set circuit breaker state."""
        state_value = {"CLOSED": 0, "OPEN": 1, "HALF_OPEN": 2}.get(state, 0)
        self.circuit_breaker_state.labels(server=server).set(state_value)

    def record_circuit_breaker_rejection(self, server: str) -> None:
        """Record circuit breaker rejection."""
        self.circuit_breaker_rejections.labels(server=server).inc()

    def record_retry_attempt(
        self, server: str, attempt: int, max_attempts: int
    ) -> None:
        """Record retry attempt."""
        self.retry_attempts.labels(server=server).inc()

    def record_http_request(
        self, method: str, endpoint: str, status_code: int, duration: float
    ) -> None:
        """Record HTTP request."""
        self.http_requests.labels(
            method=method, endpoint=endpoint, status=str(status_code)
        ).inc()
        self.http_request_duration.labels(method=method, endpoint=endpoint).observe(
            duration
        )

    def record_error(self, server: str, error_code: str, category: str) -> None:
        """Record error."""
        self.errors.labels(
            server=server, error_code=error_code, category=category
        ).inc()


def get_metrics_text() -> str:
    """
    Get metrics in Prometheus text format.

    Returns:
        Metrics as text
    """
    return generate_latest(_get_registry()).decode("utf-8")


def reset_metrics() -> None:
    """Reset metrics (for testing)."""
    global _custom_registry
    _custom_registry = CollectorRegistry()
    MetricsCollector._instance = None
```

**Step 5: Run test to verify it passes**

Run: `pytest tests/test_prometheus_metrics.py -v`
Expected: PASS (all tests green)

**Step 6: Commit**

```bash
git add src/metrics/ tests/test_prometheus_metrics.py requirements.txt
git commit -m "feat: add Prometheus metrics collection

- Add prometheus-client dependency
- Create MetricsCollector singleton for metrics
- Track token acquisition (success/failure, duration)
- Track cache hits/misses
- Track circuit breaker state and rejections
- Track retry attempts
- Track HTTP requests (method, endpoint, status, duration)
- Track errors by code and category
- Export metrics in Prometheus text format
- Support custom registry for testing

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 7: Add Metrics Endpoint to Plugin

**Files:**
- Modify: `src/dicomweb_oauth_plugin.py`
- Create: `tests/test_metrics_endpoint.py`

**Step 1: Write the failing test**

```python
# tests/test_metrics_endpoint.py
"""Tests for metrics endpoint."""
import pytest
from unittest.mock import Mock

from src.dicomweb_oauth_plugin import metrics_endpoint


def test_metrics_endpoint_returns_prometheus_format():
    """Test metrics endpoint returns Prometheus text format."""
    # Mock Orthanc module
    orthanc = Mock()

    # Call metrics endpoint
    response = metrics_endpoint(orthanc, "/dicomweb-oauth/metrics")

    # Should return tuple (body, status_code, headers)
    assert isinstance(response, tuple)
    assert len(response) == 3

    body, status_code, headers = response

    assert status_code == 200
    assert headers["Content-Type"] == "text/plain; version=0.0.4"
    assert isinstance(body, str)
    assert len(body) > 0


def test_metrics_endpoint_contains_expected_metrics():
    """Test metrics endpoint contains expected metric names."""
    orthanc = Mock()

    body, status_code, headers = metrics_endpoint(orthanc, "/dicomweb-oauth/metrics")

    # Check for expected metric families
    assert "dicomweb_oauth_token_acquisitions_total" in body
    assert "dicomweb_oauth_cache_hits_total" in body
    assert "dicomweb_oauth_circuit_breaker_state" in body
    assert "dicomweb_oauth_errors_total" in body
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_metrics_endpoint.py -v`
Expected: FAIL with "ImportError: cannot import name 'metrics_endpoint'"

**Step 3: Implement metrics endpoint**

```python
# Modify src/dicomweb_oauth_plugin.py

from src.metrics import get_metrics_text

def metrics_endpoint(orthanc: Any, uri: str) -> tuple:
    """
    Serve Prometheus metrics endpoint.

    Args:
        orthanc: Orthanc module
        uri: Request URI

    Returns:
        Tuple of (body, status_code, headers)
    """
    try:
        metrics_text = get_metrics_text()

        return (
            metrics_text,
            200,
            {"Content-Type": "text/plain; version=0.0.4"},
        )
    except Exception as e:
        logger.error(f"Failed to generate metrics: {e}")
        return (
            f"Error generating metrics: {e}",
            500,
            {"Content-Type": "text/plain"},
        )


def register_rest_callbacks(orthanc: Any) -> None:
    """Register REST API callbacks."""
    # ... existing callbacks ...

    # Metrics endpoint
    orthanc.RegisterRestCallback("/dicomweb-oauth/metrics", metrics_endpoint)

    logger.info("Registered REST API callbacks including /dicomweb-oauth/metrics")
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_metrics_endpoint.py -v`
Expected: PASS (all tests green)

**Step 5: Commit**

```bash
git add src/dicomweb_oauth_plugin.py tests/test_metrics_endpoint.py
git commit -m "feat: add Prometheus metrics HTTP endpoint

- Register /dicomweb-oauth/metrics REST callback
- Return metrics in Prometheus text format (0.0.4)
- Set correct Content-Type header
- Handle errors gracefully with 500 status
- Include all collected metrics in response

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 8: Update Error Handling to Use Error Codes

**Files:**
- Modify: `src/config_parser.py`
- Modify: `src/token_manager.py`
- Modify: `src/oauth_providers/base.py`
- Modify: `tests/test_error_handling.py`

**Step 1: Write the failing test**

```python
# Modify tests/test_error_handling.py

from src.error_codes import (
    ErrorCode,
    ConfigurationError,
    TokenAcquisitionError,
    NetworkError,
)


def test_config_error_includes_error_code():
    """Test configuration errors include structured error codes."""
    config = {"DicomWebOAuth": {"Servers": {}}}

    with pytest.raises(ConfigurationError) as exc_info:
        parser = ConfigParser(config)
        parser.get_servers()

    error = exc_info.value
    assert error.error_code == ErrorCode.CONFIG_MISSING_KEY
    assert "troubleshooting" in error.to_dict()
    assert error.documentation_url is not None


def test_token_acquisition_error_includes_error_code(mocker):
    """Test token acquisition errors include structured error codes."""
    config = {
        "TokenEndpoint": "https://test.com/token",
        "ClientId": "test-id",
        "ClientSecret": "test-secret",
    }

    manager = TokenManager("test-server", config)

    # Mock provider to fail with network error
    mock_provider = mocker.patch.object(manager.provider, "acquire_token")
    mock_provider.side_effect = requests.Timeout("Connection timeout")

    with pytest.raises(TokenAcquisitionError) as exc_info:
        manager.get_token()

    error = exc_info.value
    assert error.error_code.category.value == "NETWORK"
    assert len(error.troubleshooting_steps) > 0


def test_error_dict_includes_all_fields():
    """Test error serialization includes all required fields."""
    error = NetworkError(
        ErrorCode.NETWORK_TIMEOUT,
        "Connection timeout",
        details={"endpoint": "https://test.com"},
    )

    error_dict = error.to_dict()

    assert "error_code" in error_dict
    assert "category" in error_dict
    assert "severity" in error_dict
    assert "message" in error_dict
    assert "details" in error_dict
    assert "troubleshooting" in error_dict
    assert "documentation_url" in error_dict
    assert "http_status" in error_dict
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_error_handling.py::test_config_error_includes_error_code -v`
Expected: FAIL with "ConfigError" not matching "ConfigurationError"

**Step 3: Update config_parser.py**

```python
# Modify src/config_parser.py

from src.error_codes import ConfigurationError, ErrorCode


class ConfigParser:
    def _validate_config(self, validate_schema: bool = True) -> None:
        """Validate that required configuration structure exists."""
        if "DicomWebOAuth" not in self.config:
            raise ConfigurationError(
                ErrorCode.CONFIG_MISSING_KEY,
                "Missing 'DicomWebOAuth' section in configuration",
                details={"missing_key": "DicomWebOAuth"},
            )

        if "Servers" not in self.config["DicomWebOAuth"]:
            raise ConfigurationError(
                ErrorCode.CONFIG_MISSING_KEY,
                "Missing 'Servers' section in DicomWebOAuth configuration",
                details={"missing_key": "Servers"},
            )

        # Validate against JSON Schema if enabled
        if validate_schema:
            try:
                validate_config(self.config)
            except Exception as e:
                raise ConfigurationError(
                    ErrorCode.CONFIG_INVALID_VALUE,
                    f"Configuration validation failed: {e}",
                    details={"validation_error": str(e)},
                ) from e

    def _substitute_env_vars(self, value: str) -> str:
        """Replace ${VAR_NAME} with environment variable values."""
        pattern = r"\$\{([^}]+)\}"

        def replace_var(match: Match[str]) -> str:
            var_name = match.group(1)
            if var_name not in os.environ:
                raise ConfigurationError(
                    ErrorCode.CONFIG_ENV_VAR_MISSING,
                    f"Environment variable '{var_name}' referenced in config but not set",
                    details={"var_name": var_name},
                )
            return os.environ[var_name]

        return re.sub(pattern, replace_var, value)
```

**Step 4: Update token_manager.py**

```python
# Modify src/token_manager.py

from src.error_codes import TokenAcquisitionError as TokenError, ErrorCode, NetworkError
from src.metrics import MetricsCollector

class TokenManager:
    def _acquire_token_with_retry(self) -> Dict[str, Any]:
        """Acquire token with retry logic and metrics."""
        start_time = time.time()
        metrics = MetricsCollector.get_instance()

        for attempt in range(MAX_TOKEN_ACQUISITION_RETRIES):
            try:
                token_data = self.provider.acquire_token()

                # Record success metrics
                duration = time.time() - start_time
                metrics.record_token_acquisition(
                    server=self.server_name, success=True, duration=duration
                )

                return token_data

            except (requests.Timeout, requests.ConnectionError) as e:
                # Record failure metrics
                duration = time.time() - start_time
                metrics.record_token_acquisition(
                    server=self.server_name, success=False, duration=duration
                )

                # Determine error code
                if isinstance(e, requests.Timeout):
                    error_code = ErrorCode.NETWORK_TIMEOUT
                else:
                    error_code = ErrorCode.NETWORK_CONNECTION_ERROR

                # Record error metrics
                metrics.record_error(
                    server=self.server_name,
                    error_code=error_code.code,
                    category=error_code.category.value,
                )

                if attempt < MAX_TOKEN_ACQUISITION_RETRIES - 1:
                    delay = INITIAL_RETRY_DELAY_SECONDS * (2 ** attempt)
                    structured_logger.warning(
                        "Token acquisition retry",
                        server=self.server_name,
                        attempt=attempt + 1,
                        delay=delay,
                        error=str(e),
                    )
                    time.sleep(delay)
                    continue

                # All retries exhausted
                raise NetworkError(
                    error_code,
                    f"Failed to connect to token endpoint after {MAX_TOKEN_ACQUISITION_RETRIES} attempts",
                    details={
                        "server": self.server_name,
                        "endpoint": self.token_endpoint,
                        "attempts": MAX_TOKEN_ACQUISITION_RETRIES,
                        "error": str(e),
                    },
                ) from e

            except Exception as e:
                # Record failure metrics
                duration = time.time() - start_time
                metrics.record_token_acquisition(
                    server=self.server_name, success=False, duration=duration
                )

                # Record error metrics
                error_code = ErrorCode.TOKEN_ACQUISITION_FAILED
                metrics.record_error(
                    server=self.server_name,
                    error_code=error_code.code,
                    category=error_code.category.value,
                )

                raise TokenError(
                    error_code,
                    f"Token acquisition failed: {e}",
                    details={
                        "server": self.server_name,
                        "endpoint": self.token_endpoint,
                        "error": str(e),
                    },
                ) from e

        # Should never reach here
        raise TokenError(
            ErrorCode.TOKEN_ACQUISITION_FAILED,
            "Token acquisition failed after all retries",
            details={"server": self.server_name},
        )
```

**Step 5: Run tests to verify**

Run: `pytest tests/test_error_handling.py -v`
Expected: PASS (all tests green)

**Step 6: Commit**

```bash
git add src/config_parser.py src/token_manager.py tests/test_error_handling.py
git commit -m "feat: update error handling to use structured error codes

- Replace ConfigError with ConfigurationError including error codes
- Add error codes to all configuration validation failures
- Add error codes to token acquisition failures
- Add error codes to network errors
- Include troubleshooting steps in all errors
- Record error metrics when exceptions occur
- Provide documentation URLs for all error types

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 9: Integrate Metrics with Token Manager

**Files:**
- Modify: `src/token_manager.py`
- Create: `tests/test_token_manager_metrics.py`

**Step 1: Write the failing test**

```python
# tests/test_token_manager_metrics.py
"""Tests for token manager metrics integration."""
import pytest
from src.token_manager import TokenManager
from src.metrics import MetricsCollector, get_metrics_text


@pytest.fixture(autouse=True)
def reset_metrics():
    """Reset metrics before each test."""
    from src.metrics.prometheus import reset_metrics
    reset_metrics()
    yield


def test_token_manager_records_cache_hit(mocker):
    """Test token manager records cache hit metric."""
    config = {
        "TokenEndpoint": "https://test.com/token",
        "ClientId": "test-id",
        "ClientSecret": "test-secret",
    }

    manager = TokenManager("test-server", config)

    # Prime cache
    mock_provider = mocker.patch.object(manager.provider, "acquire_token")
    mock_provider.return_value = {"access_token": "token123", "expires_in": 3600}

    manager.get_token()

    # Get from cache
    manager.get_token()

    metrics_text = get_metrics_text()
    assert 'dicomweb_oauth_cache_hits_total{server="test-server"} 1.0' in metrics_text


def test_token_manager_records_cache_miss(mocker):
    """Test token manager records cache miss metric."""
    config = {
        "TokenEndpoint": "https://test.com/token",
        "ClientId": "test-id",
        "ClientSecret": "test-secret",
    }

    manager = TokenManager("test-server", config)

    mock_provider = mocker.patch.object(manager.provider, "acquire_token")
    mock_provider.return_value = {"access_token": "token123", "expires_in": 3600}

    # First call is cache miss
    manager.get_token()

    metrics_text = get_metrics_text()
    assert 'dicomweb_oauth_cache_misses_total{server="test-server"} 1.0' in metrics_text


def test_token_manager_records_acquisition_duration(mocker):
    """Test token manager records acquisition duration."""
    config = {
        "TokenEndpoint": "https://test.com/token",
        "ClientId": "test-id",
        "ClientSecret": "test-secret",
    }

    manager = TokenManager("test-server", config)

    mock_provider = mocker.patch.object(manager.provider, "acquire_token")
    mock_provider.return_value = {"access_token": "token123", "expires_in": 3600}

    manager.get_token()

    metrics_text = get_metrics_text()
    assert 'dicomweb_oauth_token_acquisition_duration_seconds' in metrics_text
    assert 'server="test-server"' in metrics_text
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_token_manager_metrics.py -v`
Expected: FAIL (metrics not recorded)

**Step 3: Update token_manager.py**

```python
# Modify src/token_manager.py

from src.metrics import MetricsCollector

class TokenManager:
    def get_token(self) -> str:
        """Get a valid OAuth2 access token with metrics."""
        metrics = MetricsCollector.get_instance()

        with self._lock:
            # Check if we have a valid cached token
            if self._is_token_valid():
                # Record cache hit
                metrics.record_cache_hit(self.server_name)

                structured_logger.debug(
                    "Using cached token",
                    server=self.server_name,
                    operation="get_token",
                    cached=True,
                )
                logger.debug(f"Using cached token for server '{self.server_name}'")
                assert self._cached_token is not None
                return self._cached_token

            # Record cache miss
            metrics.record_cache_miss(self.server_name)

            # Need to acquire a new token
            structured_logger.info(
                "Acquiring new token",
                server=self.server_name,
                operation="get_token",
                cached=False,
            )
            logger.info(f"Acquiring new token for server '{self.server_name}'")
            return self._acquire_token()
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_token_manager_metrics.py -v`
Expected: PASS (all tests green)

**Step 5: Commit**

```bash
git add src/token_manager.py tests/test_token_manager_metrics.py
git commit -m "feat: integrate metrics collection with token manager

- Record cache hit when returning cached token
- Record cache miss when acquiring new token
- Acquisition duration already recorded in _acquire_token_with_retry
- Add comprehensive tests for metrics integration

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 10: Add Documentation

**Files:**
- Create: `docs/RESILIENCE.md`
- Create: `docs/METRICS.md`
- Create: `docs/ERROR-CODES.md`
- Modify: `README.md`

**Step 1: Write resilience documentation**

```markdown
# docs/RESILIENCE.md
# Resilience Patterns

This plugin supports advanced resilience patterns to handle failures gracefully.

## Circuit Breaker

The circuit breaker pattern prevents cascading failures by "opening" the circuit after a threshold of failures.

### Configuration

```json
{
  "DicomWebOAuth": {
    "Servers": {
      "my-server": {
        "Url": "https://dicom.example.com",
        "TokenEndpoint": "https://auth.example.com/token",
        "ClientId": "${CLIENT_ID}",
        "ClientSecret": "${CLIENT_SECRET}",
        "ResilienceConfig": {
          "CircuitBreakerEnabled": true,
          "CircuitBreakerFailureThreshold": 5,
          "CircuitBreakerTimeout": 60
        }
      }
    }
  }
}
```

### Parameters

- `CircuitBreakerEnabled` (boolean, default: false): Enable circuit breaker
- `CircuitBreakerFailureThreshold` (integer, default: 5): Number of failures before opening circuit
- `CircuitBreakerTimeout` (number, default: 60): Seconds before attempting to close circuit

### States

- **CLOSED**: Normal operation, requests pass through
- **OPEN**: Circuit is open, requests fail fast without calling service
- **HALF_OPEN**: Testing if service recovered, one request allowed

## Retry Strategies

Configure automatic retries with various backoff strategies.

### Configuration

```json
{
  "ResilienceConfig": {
    "RetryMaxAttempts": 3,
    "RetryStrategy": "exponential",
    "RetryInitialDelay": 1.0,
    "RetryMultiplier": 2.0,
    "RetryMaxDelay": 30.0
  }
}
```

### Strategies

#### Fixed Backoff
Constant delay between retries.

```json
{
  "RetryStrategy": "fixed",
  "RetryInitialDelay": 2.0
}
```

#### Linear Backoff
Linear increase in delay.

```json
{
  "RetryStrategy": "linear",
  "RetryInitialDelay": 1.0,
  "RetryIncrement": 1.0
}
```

#### Exponential Backoff (Recommended)
Exponential increase with optional maximum.

```json
{
  "RetryStrategy": "exponential",
  "RetryInitialDelay": 1.0,
  "RetryMultiplier": 2.0,
  "RetryMaxDelay": 30.0
}
```

## Best Practices

1. **Enable circuit breaker in production** to prevent cascading failures
2. **Use exponential backoff** for retry strategy
3. **Set reasonable timeouts** (60s circuit breaker, 30s max retry delay)
4. **Monitor metrics** to tune thresholds
```

**Step 2: Write metrics documentation**

```markdown
# docs/METRICS.md
# Prometheus Metrics

The plugin exposes Prometheus metrics for monitoring.

## Metrics Endpoint

```
GET /dicomweb-oauth/metrics
```

Returns metrics in Prometheus text format.

## Available Metrics

### Token Acquisition

```
dicomweb_oauth_token_acquisitions_total{server, status}
```
Total token acquisition attempts by status (success/failure).

```
dicomweb_oauth_token_acquisition_duration_seconds{server}
```
Histogram of token acquisition duration.

### Caching

```
dicomweb_oauth_cache_hits_total{server}
```
Total cache hits.

```
dicomweb_oauth_cache_misses_total{server}
```
Total cache misses.

### Circuit Breaker

```
dicomweb_oauth_circuit_breaker_state{server}
```
Current circuit breaker state (0=CLOSED, 1=OPEN, 2=HALF_OPEN).

```
dicomweb_oauth_circuit_breaker_rejections_total{server}
```
Total requests rejected by open circuit.

### Retries

```
dicomweb_oauth_retry_attempts_total{server}
```
Total retry attempts.

### HTTP Requests

```
dicomweb_oauth_http_requests_total{method, endpoint, status}
```
Total HTTP requests by method, endpoint, and status code.

```
dicomweb_oauth_http_request_duration_seconds{method, endpoint}
```
Histogram of HTTP request duration.

### Errors

```
dicomweb_oauth_errors_total{server, error_code, category}
```
Total errors by error code and category.

## Prometheus Configuration

Add to `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'orthanc-dicomweb-oauth'
    static_configs:
      - targets: ['orthanc:8042']
    metrics_path: '/dicomweb-oauth/metrics'
    scrape_interval: 15s
```

## Grafana Dashboard

Example queries:

### Token Acquisition Success Rate
```promql
rate(dicomweb_oauth_token_acquisitions_total{status="success"}[5m])
/
rate(dicomweb_oauth_token_acquisitions_total[5m])
```

### Cache Hit Rate
```promql
rate(dicomweb_oauth_cache_hits_total[5m])
/
(rate(dicomweb_oauth_cache_hits_total[5m]) + rate(dicomweb_oauth_cache_misses_total[5m]))
```

### Circuit Breaker State
```promql
dicomweb_oauth_circuit_breaker_state
```

### P95 Token Acquisition Time
```promql
histogram_quantile(0.95, rate(dicomweb_oauth_token_acquisition_duration_seconds_bucket[5m]))
```
```

**Step 3: Write error codes documentation**

```markdown
# docs/ERROR-CODES.md
# Error Codes Reference

All errors include structured error codes with troubleshooting steps.

## Error Categories

- **CONFIGURATION** (CFG-xxx): Configuration errors
- **AUTHENTICATION** (TOK-xxx): Token acquisition errors
- **NETWORK** (NET-xxx): Network connectivity errors
- **AUTHORIZATION** (AUTH-xxx): Authorization errors
- **INTERNAL** (INT-xxx): Internal plugin errors

## Configuration Errors

### CFG-001: CONFIG_MISSING_KEY
Required configuration key is missing.

**Troubleshooting:**
1. Check that all required keys are present in DicomWebOAuth.Servers config
2. Required keys: Url, TokenEndpoint, ClientId, ClientSecret
3. Verify configuration file syntax is valid JSON

### CFG-002: CONFIG_INVALID_VALUE
Configuration value is invalid.

**Troubleshooting:**
1. Verify that URLs are properly formatted (must start with http:// or https://)
2. Check that numeric values are within valid ranges
3. Ensure boolean values are true/false

### CFG-003: CONFIG_ENV_VAR_MISSING
Referenced environment variable is not set.

**Troubleshooting:**
1. Set the missing environment variable before starting Orthanc
2. Example: `export VAR_NAME=value`
3. For Docker: use `-e VAR_NAME=value` or env_file

## Token Acquisition Errors

### TOK-001: TOKEN_ACQUISITION_FAILED
Failed to acquire OAuth2 token.

**Troubleshooting:**
1. Verify ClientId and ClientSecret are correct
2. Check that token endpoint URL is accessible
3. Ensure OAuth2 client has required permissions/grants
4. Review Orthanc logs for detailed error from provider

### TOK-002: TOKEN_EXPIRED
Cached token has expired.

**Troubleshooting:**
1. Token will be automatically refreshed on next request
2. If problem persists, check token endpoint availability

## Network Errors

### NET-001: NETWORK_TIMEOUT
Network timeout connecting to endpoint.

**Troubleshooting:**
1. Check network connectivity to the token endpoint
2. Verify firewall rules allow outbound HTTPS
3. Increase timeout if endpoint is known to be slow
4. Check if endpoint is experiencing downtime

### NET-002: NETWORK_CONNECTION_ERROR
Cannot establish connection to endpoint.

**Troubleshooting:**
1. Verify the endpoint URL is correct and accessible
2. Check DNS resolution for the endpoint hostname
3. Ensure no proxy is blocking the connection
4. Verify SSL/TLS certificates if using HTTPS

### NET-003: NETWORK_SSL_ERROR
SSL/TLS certificate verification failed.

**Troubleshooting:**
1. Verify the endpoint has a valid SSL certificate
2. Check certificate expiration date
3. For self-signed certs, set VerifySSL: false (not recommended for production)
4. Ensure system CA certificates are up to date

## Authorization Errors

### AUTH-001: AUTH_INVALID_CREDENTIALS
Invalid client credentials.

**Troubleshooting:**
1. Verify ClientId matches the registered OAuth2 client
2. Verify ClientSecret is correct and not expired
3. Check if credentials need to be rotated
4. Ensure OAuth2 client is not disabled

### AUTH-002: AUTH_INSUFFICIENT_SCOPE
Insufficient scope for requested operation.

**Troubleshooting:**
1. Add required scope to configuration Scope field
2. Verify OAuth2 client has permission for requested scope
3. Check DICOMweb server required scopes

### AUTH-003: AUTH_PROVIDER_UNAVAILABLE
Authentication provider is unavailable.

**Troubleshooting:**
1. Check if OAuth provider is experiencing an outage
2. Verify network connectivity to provider
3. Check provider status page if available
4. Consider implementing fallback authentication

## Error Response Format

```json
{
  "error_code": "TOK-001",
  "category": "AUTHENTICATION",
  "severity": "ERROR",
  "message": "Failed to acquire OAuth2 token",
  "details": {
    "server": "my-server",
    "endpoint": "https://auth.example.com/token"
  },
  "troubleshooting": [
    "Verify ClientId and ClientSecret are correct",
    "Check that token endpoint URL is accessible",
    ...
  ],
  "documentation_url": "https://github.com/rhavekost/orthanc-dicomweb-oauth/blob/main/docs/TROUBLESHOOTING.md#token-acquisition-failures",
  "http_status": 401
}
```
```

**Step 4: Update README.md**

```markdown
# Modify README.md - add new sections

## Resilience Features

The plugin includes advanced resilience patterns:

- **Circuit Breaker**: Prevent cascading failures
- **Configurable Retry**: Exponential, linear, or fixed backoff
- **Metrics**: Prometheus endpoint for monitoring

See [RESILIENCE.md](docs/RESILIENCE.md) for configuration details.

## Monitoring

Prometheus metrics available at `/dicomweb-oauth/metrics`.

Key metrics:
- Token acquisition success rate and duration
- Cache hit/miss rates
- Circuit breaker state
- Error counts by category

See [METRICS.md](docs/METRICS.md) for full details.

## Error Handling

All errors include structured error codes with:
- Error code (e.g., TOK-001, NET-002)
- Category and severity
- Troubleshooting steps
- Documentation links

See [ERROR-CODES.md](docs/ERROR-CODES.md) for reference.
```

**Step 5: Commit**

```bash
git add docs/RESILIENCE.md docs/METRICS.md docs/ERROR-CODES.md README.md
git commit -m "docs: add comprehensive documentation for new features

- Add RESILIENCE.md with circuit breaker and retry configuration
- Add METRICS.md with Prometheus metrics reference
- Add ERROR-CODES.md with complete error code reference
- Update README.md with links to new documentation
- Include configuration examples and troubleshooting guides

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 11: Run Full Test Suite

**Files:**
- None (verification step)

**Step 1: Run all tests**

Run: `pytest tests/ -v --cov=src --cov-report=term-missing`
Expected: All tests pass with high coverage

**Step 2: Run linting**

Run: `pylint src/ --fail-under=9.0`
Expected: Pass

**Step 3: Run type checking**

Run: `mypy src/`
Expected: No errors

**Step 4: Run security scan**

Run: `bandit -r src/ -f screen`
Expected: No high/medium severity issues

**Step 5: Generate coverage report**

Run: `pytest tests/ --cov=src --cov-report=html`
Expected: Coverage report generated in htmlcov/

---

## Execution Handoff

Plan complete and saved to `docs/plans/2026-02-07-architecture-resilience-monitoring-improvements.md`.

**Two execution options:**

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

**Which approach?**
