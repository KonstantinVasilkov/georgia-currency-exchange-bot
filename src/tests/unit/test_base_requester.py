"""
Tests for the BaseRequester class.

This module contains tests for the BaseRequester class, which is used to make HTTP requests.
"""

import pytest
import aiohttp
from src.utils.base_requester import BaseRequester


@pytest.mark.asyncio
async def test_get_request():
    """Test a simple GET request."""
    async with aiohttp.ClientSession() as session:
        requester = BaseRequester(session, base_url="https://httpbin.org")
        response = await requester.get(
            "/get", params={"param1": "value1", "param2": "value2"}
        )
        assert response["args"] == {"param1": "value1", "param2": "value2"}


@pytest.mark.asyncio
async def test_post_request():
    """Test a simple POST request with JSON data."""
    async with aiohttp.ClientSession() as session:
        requester = BaseRequester(session, base_url="https://httpbin.org")
        test_data = {"key1": "value1", "key2": "value2"}
        response = await requester.post("/post", json=test_data)
        assert response["json"] == test_data


@pytest.mark.asyncio
async def test_custom_headers():
    """Test sending custom headers with a request."""
    async with aiohttp.ClientSession() as session:
        requester = BaseRequester(session, base_url="https://httpbin.org")
        custom_headers = {"X-Custom-Header": "test-value"}
        response = await requester.get("/headers", headers=custom_headers)
        assert "X-Custom-Header" in response["headers"]
        assert response["headers"]["X-Custom-Header"] == "test-value"


@pytest.mark.asyncio
async def test_retry_logic():
    """Test the retry logic by requesting a URL that returns a 500 error."""
    async with aiohttp.ClientSession() as session:
        requester = BaseRequester(
            session, base_url="https://httpbin.org", retries=2, backoff_factor=0.1
        )
        with pytest.raises(Exception) as excinfo:
            await requester.get("/status/500")
        assert "500" in str(excinfo.value)
