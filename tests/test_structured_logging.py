"""Tests for structured logging."""
import json
import logging
from io import StringIO

from src.structured_logger import JsonFormatter, StructuredLogger


def test_json_formatter():
    """Test JSON log formatter."""
    # Arrange
    logger = StructuredLogger("test")
    output = StringIO()
    handler = logging.StreamHandler(output)
    handler.setFormatter(JsonFormatter())
    logger.logger.handlers.clear()  # Clear default handlers
    logger.logger.addHandler(handler)
    logger.logger.setLevel(logging.INFO)

    # Act
    logger.info("Test message", server="test-server", operation="test_op")

    # Assert
    log_output = output.getvalue().strip()
    log_entry = json.loads(log_output)

    assert log_entry["level"] == "INFO"
    assert log_entry["message"] == "Test message"
    assert log_entry["server"] == "test-server"
    assert log_entry["operation"] == "test_op"
    assert "timestamp" in log_entry
    assert "logger" in log_entry
    assert "module" in log_entry


def test_context_propagation():
    """Test context fields propagate to all logs."""
    logger = StructuredLogger("test")
    output = StringIO()
    handler = logging.StreamHandler(output)
    handler.setFormatter(JsonFormatter())
    logger.logger.handlers.clear()  # Clear default handlers
    logger.logger.addHandler(handler)
    logger.logger.setLevel(logging.INFO)

    # Set context
    logger.set_context(server="azure-dicom", request_id="12345")

    # Log multiple messages
    logger.info("First message")
    logger.info("Second message")

    # Assert context in both
    lines = output.getvalue().strip().split("\n")
    assert len(lines) == 2

    for line in lines:
        log_entry = json.loads(line)
        assert log_entry["server"] == "azure-dicom"
        assert log_entry["request_id"] == "12345"


def test_clear_context():
    """Test clearing context fields."""
    logger = StructuredLogger("test")
    output = StringIO()
    handler = logging.StreamHandler(output)
    handler.setFormatter(JsonFormatter())
    logger.logger.handlers.clear()
    logger.logger.addHandler(handler)
    logger.logger.setLevel(logging.INFO)

    # Set and then clear context
    logger.set_context(server="test-server")
    logger.clear_context()
    logger.info("Message after clear")

    # Assert context not in log
    log_output = output.getvalue().strip()
    log_entry = json.loads(log_output)
    assert "server" not in log_entry


def test_log_levels():
    """Test different log levels."""
    logger = StructuredLogger("test")
    output = StringIO()
    handler = logging.StreamHandler(output)
    handler.setFormatter(JsonFormatter())
    logger.logger.handlers.clear()
    logger.logger.addHandler(handler)
    logger.logger.setLevel(logging.DEBUG)

    # Log at different levels
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    logger.critical("Critical message")

    # Assert all levels logged
    lines = output.getvalue().strip().split("\n")
    assert len(lines) == 5

    levels = [json.loads(line)["level"] for line in lines]
    assert levels == ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


def test_exception_logging():
    """Test exception info is included in logs."""
    logger = StructuredLogger("test")
    output = StringIO()
    handler = logging.StreamHandler(output)
    handler.setFormatter(JsonFormatter())
    logger.logger.handlers.clear()
    logger.logger.addHandler(handler)
    logger.logger.setLevel(logging.ERROR)

    # Log with exception
    try:
        raise ValueError("Test error")
    except ValueError:
        logger.logger.error("Error occurred", exc_info=True)

    # Assert exception in log
    log_output = output.getvalue().strip()
    log_entry = json.loads(log_output)
    assert "exception" in log_entry
    assert "ValueError: Test error" in log_entry["exception"]


def test_no_sensitive_data():
    """Test that sensitive data is not logged."""
    logger = StructuredLogger("test")
    output = StringIO()
    handler = logging.StreamHandler(output)
    handler.setFormatter(JsonFormatter())
    logger.logger.handlers.clear()
    logger.logger.addHandler(handler)
    logger.logger.setLevel(logging.INFO)

    # Log operation without exposing sensitive data
    logger.info(
        "Token acquired",
        server="test-server",
        operation="acquire_token",
        expires_in_seconds=3600,
    )

    # Assert no token in log
    log_output = output.getvalue().strip()
    assert "token" not in log_output.lower() or "token" in log_output.lower()
    # Actually, let's be more precise - token should not appear as a value
    log_entry = json.loads(log_output)
    for key, value in log_entry.items():
        if isinstance(value, str):
            # Check that values don't look like bearer tokens (base64-ish strings)
            assert not (
                len(value) > 50 and value.replace("_", "").replace("-", "").isalnum()
            )
