"""
Tests for the logging configuration.

This module contains tests for the logging configuration, which is used to log messages
at different levels.
"""

import os
from pathlib import Path
from src.config.logging_conf import get_logger
from src.config.settings import settings


def test_logging_levels():
    """Test that the logger can log messages at different levels."""
    # Get a logger instance
    logger = get_logger("test_logging")

    # Log messages at different levels
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")

    # Test structured logging
    logger.info("Structured logging example", extra={"user_id": 123, "action": "login"})

    # Check that the log file exists
    log_dir = os.environ.get("LOG_DIR", str(settings.PROJECT_ROOT / "logs"))
    log_file = Path(log_dir) / "app.log"
    assert log_file.exists(), f"Log file {log_file} does not exist"

    # Check that the log file contains the messages
    with open(log_file, "r") as f:
        log_content = f.read()
        assert "This is a debug message" in log_content
        assert "This is an info message" in log_content
        assert "This is a warning message" in log_content
        assert "This is an error message" in log_content
        assert "Structured logging example" in log_content
