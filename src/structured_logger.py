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
