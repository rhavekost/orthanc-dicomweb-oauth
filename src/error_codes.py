"""Structured error code system for detailed error handling."""
from dataclasses import dataclass
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
            (
                "Check that all required keys are present in "
                "DicomWebOAuth.Servers config"
            ),
            "Required keys: Url, TokenEndpoint, ClientId, ClientSecret",
            "Verify configuration file syntax is valid JSON",
        ],
        documentation_url=(
            "https://github.com/rhavekost/orthanc-dicomweb-oauth/"
            "blob/main/docs/CONFIG.md#required-fields"
        ),
    )

    CONFIG_INVALID_VALUE = ErrorCodeInfo(
        code="CFG-002",
        category=ErrorCategory.CONFIGURATION,
        severity=ErrorSeverity.ERROR,
        http_status=500,
        description="Configuration value is invalid",
        troubleshooting=[
            (
                "Verify that URLs are properly formatted "
                "(must start with http:// or https://)"
            ),
            "Check that numeric values are within valid ranges",
            "Ensure boolean values are true/false",
        ],
        documentation_url=(
            "https://github.com/rhavekost/orthanc-dicomweb-oauth/"
            "blob/main/docs/CONFIG.md#field-formats"
        ),
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
        documentation_url=(
            "https://github.com/rhavekost/orthanc-dicomweb-oauth/"
            "blob/main/docs/CONFIG.md#environment-variables"
        ),
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
        documentation_url=(
            "https://github.com/rhavekost/orthanc-dicomweb-oauth/"
            "blob/main/docs/TROUBLESHOOTING.md#token-acquisition-failures"
        ),
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
        documentation_url=(
            "https://github.com/rhavekost/orthanc-dicomweb-oauth/"
            "blob/main/docs/TOKEN-MANAGEMENT.md"
        ),
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
        documentation_url=(
            "https://github.com/rhavekost/orthanc-dicomweb-oauth/"
            "blob/main/docs/TOKEN-MANAGEMENT.md#token-refresh"
        ),
    )

    TOKEN_VALIDATION_FAILED = ErrorCodeInfo(
        code="TOK-004",
        category=ErrorCategory.AUTHENTICATION,
        severity=ErrorSeverity.ERROR,
        http_status=401,
        description="Token validation failed",
        troubleshooting=[
            "Verify token signature and claims are valid",
            "Check that token hasn't been tampered with",
            "Ensure provider's public keys are accessible",
        ],
        documentation_url=(
            "https://github.com/rhavekost/orthanc-dicomweb-oauth/"
            "blob/main/docs/TOKEN-MANAGEMENT.md#validation"
        ),
    )

    TOKEN_INVALID_RESPONSE = ErrorCodeInfo(
        code="TOK-005",
        category=ErrorCategory.AUTHENTICATION,
        severity=ErrorSeverity.ERROR,
        http_status=502,
        description="Invalid response from token endpoint",
        troubleshooting=[
            "Check that token endpoint returned valid JSON",
            "Verify response contains required 'access_token' field",
            "Review provider documentation for response format",
        ],
        documentation_url=(
            "https://github.com/rhavekost/orthanc-dicomweb-oauth/"
            "blob/main/docs/OAUTH-PROVIDERS.md"
        ),
    )

    TOKEN_REFRESH_FAILED = ErrorCodeInfo(
        code="TOK-006",
        category=ErrorCategory.AUTHENTICATION,
        severity=ErrorSeverity.ERROR,
        http_status=401,
        description="Failed to refresh OAuth2 token",
        troubleshooting=[
            "Verify refresh token is still valid",
            "Check that OAuth2 client supports refresh grants",
            "Ensure refresh token hasn't been revoked",
        ],
        documentation_url=(
            "https://github.com/rhavekost/orthanc-dicomweb-oauth/"
            "blob/main/docs/TOKEN-MANAGEMENT.md#token-refresh"
        ),
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
        documentation_url=(
            "https://github.com/rhavekost/orthanc-dicomweb-oauth/"
            "blob/main/docs/TROUBLESHOOTING.md#network-errors"
        ),
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
        documentation_url=(
            "https://github.com/rhavekost/orthanc-dicomweb-oauth/"
            "blob/main/docs/TROUBLESHOOTING.md#network-errors"
        ),
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
            (
                "For self-signed certs, set VerifySSL: false "
                "(not recommended for production)"
            ),
            "Ensure system CA certificates are up to date",
        ],
        documentation_url=(
            "https://github.com/rhavekost/orthanc-dicomweb-oauth/"
            "blob/main/docs/CONFIG.md#ssl-verification"
        ),
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
        documentation_url=(
            "https://github.com/rhavekost/orthanc-dicomweb-oauth/"
            "blob/main/docs/OAUTH-PROVIDERS.md"
        ),
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
        documentation_url=(
            "https://github.com/rhavekost/orthanc-dicomweb-oauth/"
            "blob/main/docs/CONFIG.md#scopes"
        ),
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
        documentation_url=(
            "https://github.com/rhavekost/orthanc-dicomweb-oauth/"
            "blob/main/docs/TROUBLESHOOTING.md#provider-downtime"
        ),
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
