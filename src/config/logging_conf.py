"""
Logging configuration for the application using loguru.

This module configures loguru for the application, setting up log levels,
formats, and handlers based on the environment.
"""

import sys
from typing import Optional

from loguru import logger

from src.config.settings import settings

# Configure loguru
# Remove default handler
logger.remove()

# Add console handler
logger.add(
    sys.stderr,
    format=settings.LOG_FORMAT,
    level="DEBUG" if settings.DEBUG else "INFO",
    colorize=True,
    backtrace=settings.DEBUG,
    diagnose=settings.DEBUG,
)

# Add file handler for non-test environments
if not settings.ENVIRONMENT == "TEST":
    logger.add(
        settings.LOG_FILE,
        format=settings.LOG_FORMAT,
        level="DEBUG" if settings.DEBUG else "INFO",
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

        frame = inspect.currentframe().f_back  # type: ignore[union-attr]
        name = frame.f_globals["__name__"]  # type: ignore[union-attr]

    return logger.bind(name=name)


# Example usage:
# from src.config.logging_conf import get_logger
# logger = get_logger(__name__)
# logger.info("This is an info message")
# logger.debug("This is a debug message")
# logger.warning("This is a warning message")
# logger.error("This is an error message")
# logger.exception("This is an exception message")
