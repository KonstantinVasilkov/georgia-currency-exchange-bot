"""
HTTP client singleton for managing a single aiohttp.ClientSession instance.

This module provides a singleton class for managing a single aiohttp.ClientSession
instance that can be reused throughout the application.
"""

import asyncio
from typing import Optional

import aiohttp

from src.config.logging_conf import get_logger

logger = get_logger(__name__)


class HTTPClient:
    """
    Singleton class for managing a single aiohttp.ClientSession instance.

    This class ensures that only one aiohttp.ClientSession is created and reused
    throughout the application, which is more efficient than creating a new session
    for each request.

    Attributes:
        _instance (HTTPClient): The singleton instance of the class.
        _session (aiohttp.ClientSession): The aiohttp session instance.
    """

    _instance: Optional["HTTPClient"] = None
    _session: Optional[aiohttp.ClientSession] = None

    def __new__(cls):
        """
        Create a new instance of the class if one doesn't exist.

        Returns:
            HTTPClient: The singleton instance of the class.
        """
        if cls._instance is None:
            logger.debug("Creating new HTTPClient instance")
            cls._instance = super(HTTPClient, cls).__new__(cls)
            cls._instance._session = None
        return cls._instance

    @property
    def session(self) -> aiohttp.ClientSession:
        """
        Get the aiohttp session instance, creating it if it doesn't exist.

        Returns:
            aiohttp.ClientSession: The aiohttp session instance.

        Raises:
            RuntimeError: If the session is accessed outside of an event loop.
        """
        if self._session is None or self._session.closed:
            try:
                # Check if we're in an event loop
                asyncio.get_running_loop()
                logger.debug("Creating new aiohttp.ClientSession")
                self._session = aiohttp.ClientSession()
            except RuntimeError:
                logger.error(
                    "Attempted to create aiohttp.ClientSession outside of an event loop"
                )
                raise RuntimeError(
                    "HTTPClient.session was accessed outside of an event loop. "
                    "Make sure you're in an async context."
                )
        return self._session

    async def close(self):
        """
        Close the aiohttp session.

        This method should be called when the application is shutting down.
        """
        if self._session and not self._session.closed:
            logger.debug("Closing aiohttp.ClientSession")
            await self._session.close()
            self._session = None

    async def __aenter__(self):
        """
        Enter the async context manager.

        Returns:
            aiohttp.ClientSession: The aiohttp session instance.
        """
        return self.session

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Exit the async context manager.

        This does not close the session, as it may be used elsewhere.
        """
        pass


# Create a global instance of the HTTP client
http_client = HTTPClient()


def get_http_client() -> HTTPClient:
    """
    Get the singleton instance of the HTTP client.

    Returns:
        HTTPClient: The singleton instance of the HTTP client.
    """
    return http_client
