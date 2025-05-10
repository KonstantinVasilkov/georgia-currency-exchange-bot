"""
Tests for the scheduler module.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from apscheduler.schedulers.asyncio import AsyncIOScheduler  # type: ignore

from src.scheduler.scheduler import Scheduler, setup_scheduled_tasks


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
    with (
        patch("src.scheduler.scheduler.scheduler.scheduler", mock_scheduler),
        patch("src.scheduler.scheduler.sync_exchange_data") as mock_sync,
    ):
        setup_scheduled_tasks()

        # Verify that add_job was called twice (hourly + startup)
        assert mock_scheduler.add_job.call_count == 2

        # Get all calls to add_job
        calls = mock_scheduler.add_job.call_args_list

        # Verify the hourly job
        hourly_call = next(
            call for call in calls if call[1].get("id") == "sync_exchange_data"
        )
        assert hourly_call[0][0] == mock_sync  # First positional arg is the function
        assert hourly_call[0][1] == "interval"  # Second positional arg is trigger type
        assert hourly_call[1]["hours"] == 1
        assert hourly_call[1]["name"] == "Exchange Data Sync Task"

        # Verify the startup job
        startup_call = next(
            call for call in calls if call[1].get("id") == "sync_exchange_data_startup"
        )
        assert startup_call[0][0] == mock_sync
        assert startup_call[0][1] == "date"
        assert startup_call[1]["name"] == "Exchange Data Sync Task (Startup)"
