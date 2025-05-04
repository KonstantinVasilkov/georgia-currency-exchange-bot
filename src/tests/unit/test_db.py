"""Test database connection and configuration."""

from sqlmodel import Session
from sqlalchemy import text


def test_db_connection(test_engine):
    """Test that we can connect to the database and create a session."""
    with Session(test_engine) as session:
        # Try to execute a simple query
        result = session.execute(text("SELECT 1"))
        assert result.scalar() == 1

    # Verify we're using SQLite in-memory database
    assert "sqlite" in str(test_engine.url)

    # Verify the engine is working
    assert test_engine is not None
