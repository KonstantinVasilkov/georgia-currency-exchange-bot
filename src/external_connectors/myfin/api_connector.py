"""
API connector for the MyFin API.

This module provides a connector for the MyFin API, which is used to fetch exchange rate data.
"""

from typing import Dict, Any

import aiohttp

from src.config.settings import settings
from src.config.logging_conf import get_logger
from src.utils.base_requester import BaseRequester

logger = get_logger(__name__)


class MyFinApiConnector(BaseRequester):
    """
    Connector for the MyFin API.

    This class provides methods to interact with the MyFin API, specifically to fetch
    exchange rate data.

    Attributes:
        base_url (str): The base URL for the MyFin API.
        session (aiohttp.ClientSession): The aiohttp session to use for requests.
    """

    def __init__(self, http_client_session: aiohttp.ClientSession):
        """
        Initialize the MyFin API connector.

        Args:
            http_client_session: The aiohttp session to use for requests.
        """
        logger.debug(
            f"Initialized MyFinApiConnector with base URL: {settings.MYFIN_API_BASE_URL}"
        )
        super().__init__(
            session=http_client_session, base_url=settings.MYFIN_API_BASE_URL
        )

    async def get_exchange_rates(
        self,
        city: str = "tbilisi",
        include_online: bool = True,
        availability: str = "All",
    ) -> Dict[str, Any]:
        """
        Fetch exchange rate data from the MyFin API.

        Args:
            city: The city for which to fetch exchange rates. Default is "tbilisi".
            include_online: Whether to include online exchange rates. Default is True.
            availability: The availability filter. Default is "All".

        Returns:
            The exchange rate data as a dictionary.

        Raises:
            Exception: If the API request fails.
        """
        logger.info(
            f"Fetching exchange rates for city: {city}, include_online: {include_online}, availability: {availability}"
        )

        # Prepare the request payload
        payload = {
            "city": city,
            "includeOnline": include_online,
            "availability": availability,
        }

        # Make the request
        try:
            response = await self.post(
                endpoint="/exchangeRates",
                json=payload,
                headers={"Content-Type": "application/json"},
            )

            logger.info("Successfully fetched exchange rates")
            logger.debug(f"Exchange rates response: {response}")

            return response
        except Exception as e:
            logger.error(f"Failed to fetch exchange rates: {e}")
            raise

    async def get_office_coordinates(
        self,
        city: str = "tbilisi",
        include_online: bool = False,
        availability: str = "All",
    ) -> Dict[str, Any]:
        """
        Fetch office coordinates from the MyFin API.

        Args:
            office_id: The ID of the office for which to fetch coordinates.

        Returns:
            The office coordinates as a dictionary.

        Raises:
            Exception: If the API request fails.
        """
        payload = {
            "city": city,
            "includeOnline": include_online,
            "availability": availability,
        }
        # Make the request
        try:
            response = await self.post(
                endpoint="/exchangeRates/map",
                json=payload,
                headers={"Content-Type": "application/json"},
            )

            logger.info("Successfully fetched exchange rates")
            logger.debug(f"Offices response: {response}")

            return response
        except Exception as e:
            logger.error(f"Failed to fetch offices: {e}")
            raise
