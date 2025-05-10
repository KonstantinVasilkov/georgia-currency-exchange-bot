"""Test database connection and configuration."""

import pytest
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from src.db.models.organization import Organization


@pytest.mark.asyncio
async def test_db_connection(async_test_engine):
    """Test that we can connect to the database and create a session."""
    async with AsyncSession(async_test_engine) as session:
        # Try to query organizations (should be empty)
        result = await session.exec(select(Organization))
        orgs = result.all()
        assert isinstance(orgs, list)

    # Verify we're using SQLite in-memory database
    assert "sqlite" in str(async_test_engine.url)

    # Verify the engine is working
    assert async_test_engine is not None
