"""
API connector for the MyFin API.

This module provides a connector for the MyFin API, which is used to fetch exchange rate data.
"""

from typing import Dict, Any, Optional

import aiohttp

from src.config.settings import settings
from src.config.logging_conf import get_logger
from src.utils.base_requester import BaseRequester
from src.utils.http_client import get_http_client

logger = get_logger(__name__)


class MyFinApiConnector:
    """
    Connector for the MyFin API.

    This class provides methods to interact with the MyFin API, specifically to fetch
    exchange rate data.

    Attributes:
        base_url (str): The base URL for the MyFin API.
        session (aiohttp.ClientSession): The aiohttp session to use for requests.
    """

    def __init__(
        self,
        session: Optional[aiohttp.ClientSession] = None,
        base_url: Optional[str] = None,
    ):
        """
        Initialize the MyFin API connector.

        Args:
            session: The aiohttp session to use for requests. If not provided, the global
                    HTTP client's session will be used.
            base_url: The base URL for the MyFin API. If not provided, the value from settings is used.
        """
        self.base_url = base_url or settings.MYFIN_API_BASE_URL
        self.session = session or get_http_client().session
        logger.debug(f"Initialized MyFinApiConnector with base URL: {self.base_url}")

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

        # Create a requester with the injected session
        requester = BaseRequester(self.session, base_url=self.base_url)

        # Make the request
        try:
            response = await requester.post(
                "/exchangeRates",
                json=payload,
                headers={"Content-Type": "application/json"},
            )

            logger.info("Successfully fetched exchange rates")
            logger.debug(f"Exchange rates response: {response}")

            return response
        except Exception as e:
            logger.error(f"Failed to fetch exchange rates: {e}")
            raise
