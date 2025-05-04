"""
Top-level conftest.py for pytest configuration.

This file contains global pytest configuration that affects the entire test suite.
"""

import logging
import pytest
from src.tests.fixtures.db_fixtures import *  # noqa
from src.tests.mocks.api_mocks import *  # noqa

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
