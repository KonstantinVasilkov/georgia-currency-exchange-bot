"""Test database connection and configuration."""

import pytest
from sqlmodel import Session
from sqlalchemy import text
from src.config.settings import settings


def test_db_connection(engine):
    """Test that we can connect to the database and create a session."""
    with Session(engine) as session:
        # Try to execute a simple query
        result = session.execute(text("SELECT 1"))
        assert result.scalar() == 1

    # Verify we're using the test database
    assert "test_database.db" in settings.DATABASE_URL

    # Verify the engine is working
    assert engine is not None
