"""
Simple test script to verify that the logging configuration works correctly.
"""

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.config.logging_conf import get_logger

# Get a logger instance
logger = get_logger("test_logging")

# Log messages at different levels
logger.debug("This is a debug message")
logger.info("This is an info message")
logger.warning("This is a warning message")
logger.error("This is an error message")

# Test structured logging
logger.info("Structured logging example", extra={"user_id": 123, "action": "login"})

print("Logging test completed. Check the console output and the logs directory.")