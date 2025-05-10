"""
Datetime utility functions for timezone handling.

Provides helpers to ensure all datetimes are UTC-aware.
"""

from datetime import datetime, UTC
from typing import Any


def to_utc(dt: Any) -> datetime:
    """
    Convert a datetime object to a UTC-aware datetime.

    Args:
        dt: The datetime object to convert. Can be naive or timezone-aware, or a string.

    Returns:
        A timezone-aware datetime in UTC.

    Raises:
        ValueError: If the input cannot be parsed as a datetime.
    """
    if isinstance(dt, str):
        # Try parsing ISO format
        try:
            dt = datetime.fromisoformat(dt)
        except Exception as exc:
            raise ValueError(f"Cannot parse datetime string: {dt}") from exc
    if not isinstance(dt, datetime):
        raise ValueError(f"Input is not a datetime: {dt}")
    if dt.tzinfo is None:
        # Assume naive datetimes are in local time, convert to UTC
        # If you want to assume naive datetimes are UTC, just use dt.replace(tzinfo=UTC)
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)
