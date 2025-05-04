"""
Top-level conftest.py for pytest configuration.

This file contains global pytest configuration that affects the entire test suite.
"""

import logging
import pytest
from src.tests.mocks.api_mocks import *  # noqa
from typing import Generator
from alembic.config import Config
from alembic import command
from sqlmodel import Session, create_engine, SQLModel
from sqlalchemy.pool import StaticPool
from sqlalchemy import text, inspect


# Configure pytest-asyncio
pytest_plugins = ["pytest_asyncio"]


def pytest_addoption(parser):
    """Add custom command line options to pytest."""
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="run integration tests",
    )


# Configure logging for tests
@pytest.fixture(autouse=True)
def setup_logging():
    """Configure logging for all tests."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)8s] %(message)s (%(filename)s:%(lineno)s)",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


# Skip integration tests by default
def pytest_configure(config):
    """Configure pytest to skip integration tests by default."""
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    if not config.getoption("--run-integration"):
        setattr(config.option, "markexpr", "not integration")


def drop_all_tables(engine):
    """
    Drop all tables in the database.

    Args:
        engine: SQLAlchemy engine instance.
    """
    inspector = inspect(engine)
    with engine.begin() as conn:
        # Get all table names
        table_names = inspector.get_table_names()

        # Drop each table
        for table_name in table_names:
            conn.execute(text(f"DROP TABLE IF EXISTS {table_name}"))

        conn.commit()


@pytest.fixture(scope="session")
def test_engine():
    """
    Create a test database engine using in-memory SQLite.

    Returns:
        Engine: The test database engine.
    """
    # Use a shared in-memory SQLite database
    # The "?mode=memory&cache=shared" part makes it shared between connections
    engine = create_engine(
        "sqlite:///file:memdb1?mode=memory&cache=shared&uri=true",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,  # Set to True for debugging SQL queries
    )

    try:
        # Drop all existing tables first
        drop_all_tables(engine)

        # Create all tables using SQLModel metadata
        SQLModel.metadata.create_all(engine)

        # Initialize Alembic and stamp the current version
        alembic_cfg = Config("alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", str(engine.url))
        command.stamp(alembic_cfg, "head")

        yield engine
    finally:
        # Clean up by dropping all tables
        drop_all_tables(engine)


@pytest.fixture(scope="function")
def db_session(test_engine) -> Generator[Session, None, None]:
    """
    Create a test database session.

    Args:
        test_engine: The test database engine.

    Yields:
        Session: The test database session.
    """
    connection = test_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    try:
        yield session
    finally:
        session.close()
        # Rollback the transaction to clean up any changes
        transaction.rollback()
        connection.close()


@pytest.fixture(autouse=True)
def cleanup_tables(test_engine):
    """
    Clean up tables after each test.

    This fixture runs automatically after each test to ensure a clean state.
    """
    yield  # Run the test
    with test_engine.connect() as conn:
        # Delete all data from tables
        conn.execute(text("DELETE FROM rate"))
        conn.execute(text("DELETE FROM office"))
        conn.execute(text("DELETE FROM organization"))
        conn.commit()
