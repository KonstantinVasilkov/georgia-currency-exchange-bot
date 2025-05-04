"""
Main entry point for the Georgia Currency Exchange Bot.

This module initializes and runs both the Telegram bot and the scheduler
for background tasks.
"""

import asyncio
import signal
import sys
from typing import Any

from alembic.config import Config
from alembic import command

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
    logger.info("Application shut down successfully")
    sys.exit(0)


def run_migrations() -> None:
    """Run database migrations using Alembic."""
    try:
        # Create Alembic configuration
        alembic_cfg = Config("alembic.ini")

        # Run the migration
        command.upgrade(alembic_cfg, "head")
        logger.info("Database migrations completed successfully")
    except Exception as e:
        logger.error(f"Error running database migrations: {e}")
        raise


async def main() -> None:
    """Main entry point for the application."""
    try:
        # Set up signal handlers
        signal.signal(signal.SIGINT, handle_shutdown)
        signal.signal(signal.SIGTERM, handle_shutdown)

        # Run database migrations
        run_migrations()

        # Set up and start the scheduler
        setup_scheduled_tasks()
        scheduler.start()
        logger.info("Scheduler started successfully")

        # TODO: Initialize and start the Telegram bot here
        # This will be implemented in a future update

        # Keep the script running
        while True:
            await asyncio.sleep(1)

    except Exception as e:
        logger.error(f"Error in application: {e}")
        raise
    finally:
        scheduler.shutdown()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Application stopped due to error: {e}")
        sys.exit(1)
