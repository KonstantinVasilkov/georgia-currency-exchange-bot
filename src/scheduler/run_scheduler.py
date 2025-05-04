"""
Entry point script for running the scheduler.

This script initializes and runs the scheduler with all configured tasks.
"""

import asyncio
import signal
import sys
from typing import Any

from src.config.logging_conf import get_logger
from src.scheduler.scheduler import scheduler, setup_scheduled_tasks

logger = get_logger(__name__)


def handle_shutdown(signum: int, frame: Any) -> None:
    """
    Handle shutdown signals.

    Args:
        signum: The signal number.
        frame: The current stack frame.
    """
    logger.info(f"Received signal {signum}, shutting down...")
    scheduler.shutdown()
    logger.info("Scheduler shut down successfully")
    # Force exit the program
    sys.exit(0)


async def main() -> None:
    """Main entry point for the scheduler."""
    try:
        # Set up signal handlers
        signal.signal(signal.SIGINT, handle_shutdown)
        signal.signal(signal.SIGTERM, handle_shutdown)

        # Set up scheduled tasks
        setup_scheduled_tasks()

        # Start the scheduler
        scheduler.start()
        logger.info("Scheduler started successfully")

        # Keep the script running
        while True:
            await asyncio.sleep(1)

    except Exception as e:
        logger.error(f"Error in scheduler: {e}")
        raise
    finally:
        scheduler.shutdown()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Scheduler stopped due to error: {e}")
        sys.exit(1)
