import os
import sys
import pytest
from pathlib import Path
from sqlmodel import Session

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.db.session import get_engine, create_db_and_tables  # noqa: E402
from src.config.settings import settings, PROJECT_ROOT  # noqa: E402


@pytest.fixture(scope="session")
def db_engine():
    """
    Create a test database engine.
    This fixture has session scope, so it will be created once per test session.
    """
    # Make sure we're using the test database
    assert "test_database.db" in settings.DATABASE_URL, "Not using test database!"

    # Get the engine
    engine = get_engine()

    # Create all tables
    create_db_and_tables()

    yield engine

    # Teardown: Remove the test database file after all tests are done
    test_db_path = Path(PROJECT_ROOT) / "src" / "db" / "test_database.db"
    if test_db_path.exists():
        os.remove(test_db_path)


@pytest.fixture
def db_session(db_engine):
    """
    Create a new database session for a test.
    This fixture has function scope, so it will be created once per test function.
    """
    # Connect to the database
    connection = db_engine.connect()

    # Begin a transaction
    transaction = connection.begin()

    # Create a session
    session = Session(bind=connection)

    yield session

    # Teardown: Roll back the transaction and close the session
    session.close()
    transaction.rollback()
    connection.close()
