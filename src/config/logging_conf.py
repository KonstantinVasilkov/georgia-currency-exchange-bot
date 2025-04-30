"""
Logging configuration for the application using loguru.

This module configures loguru for the application, setting up log levels,
formats, and handlers based on the environment.
"""

import os
import sys
from typing import Optional

from loguru import logger

from src.config.settings import settings, PROJECT_ROOT

# Define log directory
LOG_DIR = os.environ.get("LOG_DIR", str(PROJECT_ROOT / "logs"))
os.makedirs(LOG_DIR, exist_ok=True)

# Define log file path
LOG_FILE = os.path.join(LOG_DIR, "app.log")

# Define log level based on environment
LOG_LEVEL = os.environ.get("LOG_LEVEL", "DEBUG" if settings.DEBUG else "INFO")

# Define log format
LOG_FORMAT = os.environ.get(
    "LOG_FORMAT",
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
    "<level>{message}</level>",
)

# Configure loguru
# Remove default handler
logger.remove()

# Add console handler
logger.add(
    sys.stderr,
    format=LOG_FORMAT,
    level=LOG_LEVEL,
    colorize=True,
    backtrace=settings.DEBUG,
    diagnose=settings.DEBUG,
)

# Add file handler for non-test environments
if not settings.ENVIRONMENT == "TEST":
    logger.add(
        LOG_FILE,
        format=LOG_FORMAT,
        level=LOG_LEVEL,
        rotation="10 MB",  # Rotate when file reaches 10 MB
        retention="1 month",  # Keep logs for 1 month
        compression="zip",  # Compress rotated logs
        backtrace=settings.DEBUG,
        diagnose=settings.DEBUG,
    )


def get_logger(name: Optional[str] = None):
    """
    Get a logger instance with the given name.

    Args:
        name: The name of the logger. If None, the calling module's name is used.

    Returns:
        A logger instance.
    """
    if name is None:
        # Get the calling module's name
        import inspect

        frame = inspect.currentframe().f_back
        name = frame.f_globals["__name__"]

    return logger.bind(name=name)


# Example usage:
# from src.config.logging_conf import get_logger
# logger = get_logger(__name__)
# logger.info("This is an info message")
# logger.debug("This is a debug message")
# logger.warning("This is a warning message")
# logger.error("This is an error message")
# logger.exception("This is an exception message")
