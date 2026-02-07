"""Structured logging for OAuth plugin with secret redaction."""
import json
import logging
import re
import sys
import uuid
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict, Optional

# Secret patterns to redact
SECRET_PATTERNS = [
    (
        re.compile(
            r"(client_secret|api_key|password|secret|token)([\s=:]+)[\w\-\.]+",
            re.IGNORECASE,
        ),
        r"\1\2***REDACTED***",
    ),
    (re.compile(r"Bearer\s+[\w\-\.]+", re.IGNORECASE), "Bearer ***REDACTED***"),
    (
        re.compile(r"Authorization:\s*Bearer\s+[\w\-\.]+", re.IGNORECASE),
        "Authorization: Bearer ***REDACTED***",
    ),
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
            # Ensure log directory exists
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = RotatingFileHandler(
                filename=log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding="utf-8",
            )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

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
