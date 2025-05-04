"""
Tests for the scheduler module.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from apscheduler.schedulers.asyncio import AsyncIOScheduler  # type: ignore

from src.scheduler.scheduler import Scheduler, log_scheduled_task, setup_scheduled_tasks


@pytest.fixture
def mock_scheduler() -> MagicMock:
    """
    Create a mock scheduler.

    Returns:
        MagicMock: A mock scheduler instance.
    """
    return MagicMock(spec=AsyncIOScheduler)


@pytest.fixture
def scheduler_instance(mock_scheduler: MagicMock) -> Scheduler:
    """
    Create a scheduler instance with a mock scheduler.

    Args:
        mock_scheduler: A mock scheduler instance.

    Returns:
        Scheduler: A scheduler instance with the mock scheduler.
    """
    with patch("src.scheduler.scheduler.AsyncIOScheduler", return_value=mock_scheduler):
        return Scheduler()


@pytest.mark.asyncio
async def test_log_scheduled_task() -> None:
    """Test that log_scheduled_task logs the current time."""
    with patch("src.scheduler.scheduler.logger") as mock_logger:
        await log_scheduled_task()
        mock_logger.info.assert_called_once()
        # Verify that the log message contains a timestamp
        log_message = mock_logger.info.call_args[0][0]
        assert isinstance(log_message, str)
        assert "Scheduled task executed at" in log_message


def test_scheduler_initialization(
    scheduler_instance: Scheduler, mock_scheduler: MagicMock
) -> None:
    """
    Test that the scheduler is initialized correctly.

    Args:
        scheduler_instance: A scheduler instance.
        mock_scheduler: A mock scheduler instance.
    """
    assert scheduler_instance.scheduler == mock_scheduler
    mock_scheduler.start.assert_not_called()


def test_scheduler_start(
    scheduler_instance: Scheduler, mock_scheduler: MagicMock
) -> None:
    """
    Test that the scheduler starts correctly.

    Args:
        scheduler_instance: A scheduler instance.
        mock_scheduler: A mock scheduler instance.
    """
    mock_scheduler.running = False
    scheduler_instance.start()
    mock_scheduler.start.assert_called_once()


def test_scheduler_shutdown(
    scheduler_instance: Scheduler, mock_scheduler: MagicMock
) -> None:
    """
    Test that the scheduler shuts down correctly.

    Args:
        scheduler_instance: A scheduler instance.
        mock_scheduler: A mock scheduler instance.
    """
    mock_scheduler.running = True
    scheduler_instance.shutdown()
    mock_scheduler.shutdown.assert_called_once()


def test_scheduler_add_job(
    scheduler_instance: Scheduler, mock_scheduler: MagicMock
) -> None:
    """
    Test that jobs can be added to the scheduler.

    Args:
        scheduler_instance: A scheduler instance.
        mock_scheduler: A mock scheduler instance.
    """
    mock_func = AsyncMock()
    scheduler_instance.add_job(mock_func, "interval", minutes=1)
    mock_scheduler.add_job.assert_called_once_with(
        mock_func,
        "interval",
        minutes=1,
    )


def test_setup_scheduled_tasks(mock_scheduler: MagicMock) -> None:
    """
    Test that scheduled tasks are set up correctly.

    Args:
        mock_scheduler: A mock scheduler instance.
    """
    with patch("src.scheduler.scheduler.scheduler.scheduler", mock_scheduler):
        setup_scheduled_tasks()
        mock_scheduler.add_job.assert_called_once()
        # Verify that the job was added with the correct function and trigger
        call_args = mock_scheduler.add_job.call_args[0]
        assert call_args[0] == log_scheduled_task
        assert call_args[1] == "cron"
        assert mock_scheduler.add_job.call_args[1]["minute"] == "*"
        assert mock_scheduler.add_job.call_args[1]["id"] == "test_task"
        assert mock_scheduler.add_job.call_args[1]["name"] == "Test Logging Task"
