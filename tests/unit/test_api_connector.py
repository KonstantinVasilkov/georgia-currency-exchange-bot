"""
Test for the MyFin API connector.

This module contains tests for the MyFinApiConnector class.
"""

import pytest
from src.external_connectors.myfin.api_connector import MyFinApiConnector
from src.utils.http_client import get_http_client
from src.config.logging_conf import get_logger

logger = get_logger(__name__)


@pytest.mark.asyncio
async def test_api_connector():
    """Test that the MyFinApiConnector can fetch exchange rates."""
    logger.info("Testing MyFinApiConnector...")

    # Get the HTTP client
    http_client = get_http_client()

    try:
        # Create an instance of the MyFinApiConnector with the HTTP client's session
        connector = MyFinApiConnector(http_client_session=http_client.session)

        # Log the base URL
        logger.info(f"Using base URL: {connector.base_url}")

        # Fetch exchange rates with default parameters
        logger.info("Fetching exchange rates with default parameters...")
        exchange_rates = await connector.get_exchange_rates()

        # Log the result (in a real scenario, we would process the data)
        logger.info("Successfully fetched exchange rates")
        logger.info(
            f"Received {len(exchange_rates) if isinstance(exchange_rates, list) else 'non-list'} data"
        )

        # Assert that we received some data
        assert exchange_rates is not None

    finally:
        # Close the HTTP client session
        await http_client.close()

    logger.info("Test completed.")
