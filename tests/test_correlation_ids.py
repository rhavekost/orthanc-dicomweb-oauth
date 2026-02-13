"""Tests for correlation ID tracking."""
import json
import logging
from io import StringIO
from typing import cast

from src.structured_logger import StructuredLogger


def test_correlation_id_in_logs() -> None:
    """Test that correlation ID appears in all log entries."""
    # Create logger with string stream
    stream = StringIO()
    logger = StructuredLogger(name="test-correlation")
    handler = cast(logging.StreamHandler[StringIO], logger.logger.handlers[0])
    handler.stream = stream

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


def test_correlation_id_cleared() -> None:
    """Test that correlation ID can be cleared."""
    stream = StringIO()
    logger = StructuredLogger(name="test-clear")
    handler = cast(logging.StreamHandler[StringIO], logger.logger.handlers[0])
    handler.stream = stream

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


def test_auto_generate_correlation_id() -> None:
    """Test automatic correlation ID generation."""
    logger = StructuredLogger(name="test-auto")

    # Generate correlation ID
    correlation_id = logger.generate_correlation_id()

    # Should be UUID format
    assert len(correlation_id) == 36  # UUID4 format
    assert correlation_id.count("-") == 4
