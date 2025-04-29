"""
Tests for the SyncService module.

This module contains tests for the SyncService module, which is used to fetch and
synchronize exchange rate data.
"""

import pytest
from src.services.SyncService import sync_exchange_data


@pytest.mark.asyncio
async def test_sync_exchange_data():
    """Test that the sync_exchange_data function runs without errors."""
    # Call the function
    await sync_exchange_data()

    # If we get here without an exception, the test passes
    assert True
