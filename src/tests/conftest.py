"""
Top-level conftest.py for pytest configuration.

This file contains global pytest configuration that affects the entire test suite.
"""

import logging
import pytest
import pytest_asyncio
from src.tests.mocks.api_mocks import *  # noqa
from sqlmodel import SQLModel
from sqlalchemy.pool import StaticPool
from sqlalchemy import text, inspect
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
import asyncio


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


@pytest_asyncio.fixture(scope="session")
async def async_test_engine():
    engine = create_async_engine(
        "sqlite+aiosqlite:///file:memdb1?mode=memory&cache=shared&uri=true",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(async_test_engine):
    async with AsyncSession(async_test_engine, expire_on_commit=False) as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture(autouse=True)
async def cleanup_tables(async_test_engine):
    """
    Clean up tables after each test.

    This fixture runs automatically after each test to ensure a clean state.
    """
    yield  # Run the test
    async with async_test_engine.begin() as conn:
        await conn.execute(text("DELETE FROM rate"))
        await conn.execute(text("DELETE FROM office"))
        await conn.execute(text("DELETE FROM organization"))


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the session scope."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
