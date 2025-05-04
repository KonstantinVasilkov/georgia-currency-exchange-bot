"""
Scheduler module for managing background tasks.

This module provides functionality for scheduling and managing background tasks
using APScheduler.
"""

from typing import Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler  # type: ignore
from apscheduler.triggers.cron import CronTrigger  # type: ignore

from src.config.logging_conf import get_logger
from src.services.sync_service import sync_exchange_data

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


def setup_scheduled_tasks() -> None:
    """Set up all scheduled tasks."""
    # Add sync task to run every hour
    scheduler.add_job(
        sync_exchange_data,
        trigger="interval",
        hours=1,  # Run every hour
        id="sync_exchange_data",
        name="Exchange Data Sync Task",
    )

    # Also add a one-time task to run immediately on startup
    scheduler.add_job(
        sync_exchange_data,
        trigger="date",  # Run once at a specific time (now)
        id="sync_exchange_data_startup",
        name="Exchange Data Sync Task (Startup)",
    )

    logger.info("Scheduled tasks set up")
