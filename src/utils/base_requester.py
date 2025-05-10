"""
BaseRequester module for making HTTP requests with retry logic, rate limiting, and pre-request hooks.

This module provides a flexible and extensible base for making HTTP requests with retry logic,
optional rate limiting, and support for pre-request hooks.
"""

import asyncio
import time
from collections.abc import Awaitable, Callable
from enum import Enum
from typing import Any, Optional, Union, Dict, Tuple

import aiohttp
from aiohttp import ClientResponseError
from multidict import CIMultiDictProxy

from src.config.logging_conf import get_logger

logger = get_logger(__name__)


class HTTPMethod(str, Enum):
    """HTTP methods enum."""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


class AbstractRateLimiter:
    """Abstract base class for rate limiters."""

    async def acquire(self) -> None:
        """Acquire a token from the rate limiter."""
        raise NotImplementedError("Subclasses must implement acquire()")


class BaseRequester:
    """
    BaseRequester provides a flexible and extensible base for making HTTP requests with retry logic,
    optional rate limiting, and support for pre-request hooks.

    This class is designed to interact with external APIs or HTTP endpoints, simplifying the process of
    making asynchronous HTTP requests. With built-in features like retry mechanisms, customizable headers,
    and optional rate limiting, it helps manage communication with third-party services gracefully.
    The base URL and custom headers can be set globally within the class, and individual requests allow
    fine-tuning of request details.

    Attributes:
        session (aiohttp.ClientSession): The aiohttp session used for making HTTP requests.
        base_url (str): The base URL to use for all HTTP requests.
        headers (dict[str, str]): Default headers applied to all HTTP requests unless overridden.
        retries (int): Number of retries if a request fails due to certain errors.
        backoff_factor (float): Exponential backoff interval between retries.
        retry_status_codes (list[int]): List of status codes for which retries are allowed.
        pre_request_hook (Callable[..., Awaitable[None]] | None): An optional asynchronous function executed before each request.
        rate_limiter (AbstractRateLimiter | None): Optional rate limiter controlling request rate.
    """

    def __init__(
        self,
        session: aiohttp.ClientSession,
        base_url: str = "",
        headers: Optional[Dict[str, str]] = None,
        retries: int = 3,
        backoff_factor: float = 0.5,
        retry_status_codes: Optional[list[int]] = None,
        pre_request_hook: Optional[Callable[..., Awaitable[None]]] = None,
        rate_limiter: Optional[AbstractRateLimiter] = None,
    ) -> None:
        self.session = session
        self.base_url = base_url.rstrip("/")
        self.headers = headers or {}
        self.retries = retries
        self.backoff_factor = backoff_factor
        self.retry_status_codes = retry_status_codes or []
        self.pre_request_hook = pre_request_hook
        self._is_hook_running = False
        self.rate_limiter = rate_limiter

    async def _send_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        json: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
        return_headers: bool = False,
    ) -> Union[Any, Tuple[Any, CIMultiDictProxy[str]]]:
        """
        Send an HTTP request with retry logic.

        Args:
            method: HTTP method to use (GET, POST, etc.)
            endpoint: URL endpoint to send the request to
            params: Query parameters to include in the request
            data: Form data to include in the request
            json: JSON data to include in the request
            headers: Headers to include in the request
            return_headers: Whether to return the response headers along with the response body

        Returns:
            The response body, or a tuple of (response body, response headers) if return_headers is True

        Raises:
            aiohttp.ClientError: If the request fails after all retries
            Exception: If the request fails for any other reason after all retries
        """
        if isinstance(self.rate_limiter, AbstractRateLimiter):
            await self.rate_limiter.acquire()
        url = self._build_url(endpoint)

        attempt = 0

        while attempt < self.retries:
            try:
                if self.pre_request_hook and not self._is_hook_running:
                    logger.debug(
                        "Executing pre-request hook: %s", self.pre_request_hook.__name__
                    )
                    self._is_hook_running = True
                    await self.pre_request_hook()
                    self._is_hook_running = False

                combined_headers = {**self.headers, **(headers or {})}
                logger.info(
                    f"Attempt {attempt + 1} | {method.upper()} {url} | "
                    f"Params: {params} | Data: {data} | JSON: {json} | Headers: {combined_headers}"
                )
                start_time = time.perf_counter()
                async with self.session.request(
                    method,
                    url,
                    params=params,
                    data=data,
                    json=json,
                    headers=combined_headers,
                ) as response:
                    end_time = time.perf_counter()
                    elapsed_time = end_time - start_time
                    logger.info(f"Request to {url} took {elapsed_time:.4f} seconds.")

                    content_type = response.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        response_content = await response.json()
                    elif "text/html" in content_type:
                        response_content = await response.text()
                    else:
                        # For other content types, try to get text first, then fallback to bytes
                        try:
                            response_content = await response.text()
                        except UnicodeDecodeError:
                            response_content = await response.read()
                            logger.warning(
                                "Response content could not be decoded as text. Returning bytes."
                            )

                    logger.info(f"Response Status: {response.status}")
                    # logger.debug(f"Response Content: {response_content}")

                    response.raise_for_status()

                    if return_headers:
                        return response_content, response.headers
                    else:
                        return response_content
            except ClientResponseError as e:
                logger.warning(
                    f"HTTP error on {method.upper()} {url}: {e.status} - {e.message}"
                )
                should_retry = False
                if e.status in self.retry_status_codes:
                    should_retry = True
                    logger.info(
                        f"Status code {e.status} is in custom retry list and will be retried."
                    )
                elif e.status >= 500:
                    should_retry = True
                    logger.info(
                        f"Status code {e.status} is a server error and will be retried."
                    )

                if should_retry:
                    attempt += 1
                    if attempt < self.retries:
                        sleep_time = self.backoff_factor * (2 ** (attempt - 1))
                        logger.info(f"Retrying in {sleep_time} seconds...")
                        await asyncio.sleep(sleep_time)
                    else:
                        logger.error(f"Max retries reached for {method.upper()} {url}.")
                        raise
                else:
                    raise
            except aiohttp.ClientError as e:
                logger.error(f"Client error on {method.upper()} {url}: {e!s}")
                attempt += 1
                if attempt < self.retries:
                    sleep_time = self.backoff_factor * (2 ** (attempt - 1))
                    logger.info(f"Retrying in {sleep_time} seconds...")
                    await asyncio.sleep(sleep_time)
                else:
                    logger.error(f"Max retries reached for {method.upper()} {url}.")
                    raise
            except Exception as e:
                logger.exception(f"Unexpected error on {method.upper()} {url}: {e!s}")
                raise

        raise Exception(
            f"Failed to {method.upper()} {url} after {self.retries} attempts."
        )

    def _build_url(self, endpoint: str) -> str:
        """
        Build a full URL from the base URL and endpoint.

        Args:
            endpoint: The endpoint to append to the base URL

        Returns:
            The full URL
        """
        return (
            endpoint
            if endpoint.startswith(("http://", "https://"))
            else f"{self.base_url}/{endpoint.lstrip('/')}"
        )

    async def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        return_headers: bool = False,
    ) -> Any:
        """
        Send a GET request.

        Args:
            endpoint: URL endpoint to send the request to
            params: Query parameters to include in the request
            headers: Headers to include in the request
            return_headers: Whether to return the response headers along with the response body

        Returns:
            The response body, or a tuple of (response body, response headers) if return_headers is True
        """
        return await self._send_request(
            HTTPMethod.GET,
            endpoint,
            params=params,
            headers=headers,
            return_headers=return_headers,
        )

    async def post(
        self,
        endpoint: str,
        data: Optional[Any] = None,
        json: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
        return_headers: bool = False,
    ) -> Any:
        """
        Send a POST request.

        Args:
            endpoint: URL endpoint to send the request to
            data: Form data to include in the request
            json: JSON data to include in the request
            headers: Headers to include in the request
            return_headers: Whether to return the response headers along with the response body

        Returns:
            The response body, or a tuple of (response body, response headers) if return_headers is True
        """
        return await self._send_request(
            HTTPMethod.POST,
            endpoint,
            data=data,
            json=json,
            headers=headers,
            return_headers=return_headers,
        )

    async def put(
        self,
        endpoint: str,
        data: Optional[Any] = None,
        json: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
        return_headers: bool = False,
    ) -> Any:
        """
        Send a PUT request.

        Args:
            endpoint: URL endpoint to send the request to
            data: Form data to include in the request
            json: JSON data to include in the request
            headers: Headers to include in the request
            return_headers: Whether to return the response headers along with the response body

        Returns:
            The response body, or a tuple of (response body, response headers) if return_headers is True
        """
        return await self._send_request(
            HTTPMethod.PUT,
            endpoint,
            data=data,
            json=json,
            headers=headers,
            return_headers=return_headers,
        )

    async def delete(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        return_headers: bool = False,
    ) -> Any:
        """
        Send a DELETE request.

        Args:
            endpoint: URL endpoint to send the request to
            params: Query parameters to include in the request
            headers: Headers to include in the request
            return_headers: Whether to return the response headers along with the response body

        Returns:
            The response body, or a tuple of (response body, response headers) if return_headers is True
        """
        return await self._send_request(
            HTTPMethod.DELETE,
            endpoint,
            params=params,
            headers=headers,
            return_headers=return_headers,
        )

    async def patch(
        self,
        endpoint: str,
        data: Optional[Any] = None,
        json: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
        return_headers: bool = False,
    ) -> Any:
        """
        Send a PATCH request.

        Args:
            endpoint: URL endpoint to send the request to
            data: Form data to include in the request
            json: JSON data to include in the request
            headers: Headers to include in the request
            return_headers: Whether to return the response headers along with the response body

        Returns:
            The response body, or a tuple of (response body, response headers) if return_headers is True
        """
        return await self._send_request(
            HTTPMethod.PATCH,
            endpoint,
            data=data,
            json=json,
            headers=headers,
            return_headers=return_headers,
        )
