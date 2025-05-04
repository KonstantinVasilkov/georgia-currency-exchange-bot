"""
Scheduler package for managing background tasks.

This package provides functionality for scheduling and running background tasks
using APScheduler.
"""

from src.scheduler.scheduler import Scheduler, setup_scheduled_tasks

__all__ = ["Scheduler", "setup_scheduled_tasks"]
