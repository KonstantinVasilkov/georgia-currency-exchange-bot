"""
Scheduler module for managing background tasks.

This module provides functionality for scheduling and managing background tasks
using APScheduler.
"""

from datetime import datetime, timezone
from typing import Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler  # type: ignore
from apscheduler.triggers.cron import CronTrigger  # type: ignore

from src.config.logging_conf import get_logger

logger = get_logger(__name__)


class Scheduler:
    """
    Scheduler class for managing background tasks.
    """

    def __init__(self) -> None:
        """Initialize the scheduler."""
        self.scheduler = AsyncIOScheduler()
        logger.info("Scheduler initialized")

    def start(self) -> None:
        """Start the scheduler."""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Scheduler started")

    def shutdown(self) -> None:
        """Shutdown the scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler shut down")

    def add_job(
        self,
        func: Any,
        trigger: str | CronTrigger,
        **trigger_args: Any,
    ) -> None:
        """
        Add a job to the scheduler.

        Args:
            func: The function to execute.
            trigger: The trigger type (e.g., 'cron', 'interval', 'date').
            **trigger_args: Additional arguments for the trigger.
        """
        self.scheduler.add_job(func, trigger, **trigger_args)
        logger.info(f"Added job {func.__name__} with trigger {trigger}")


# Create a global scheduler instance
scheduler = Scheduler()


async def log_scheduled_task() -> None:
    """
    A simple scheduled task that logs the current time.

    This is used for testing the scheduler functionality.
    """
    current_time = datetime.now(timezone.utc)
    logger.info(f"Scheduled task executed at {current_time.isoformat()}")


def setup_scheduled_tasks() -> None:
    """Set up all scheduled tasks."""
    # Add a test task that runs every minute
    scheduler.add_job(
        log_scheduled_task,
        trigger="cron",
        minute="*",  # Run every minute
        id="test_task",
        name="Test Logging Task",
    )
    logger.info("Scheduled tasks set up")
