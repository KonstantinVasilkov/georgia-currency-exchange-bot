import pytest
from sqlmodel import select
from src.config.settings import settings

def test_db_connection(db_engine):
    """
    Test the database connection using the test database.

    Args:
        db_engine: SQLAlchemy engine fixture from conftest.py
    """
    # Verify we're using the test database
    assert "test_database.db" in settings.DATABASE_URL

    # Verify the engine is working
    assert db_engine is not None

    # Verify the connection works
    with db_engine.connect() as conn:
        result = conn.execute(select(1)).scalar_one()
        assert result == 1
