"""
Test script for the BaseRequester class.

This script tests the functionality of the BaseRequester class by making
requests to a public API (httpbin.org) and verifying the responses.
"""

import asyncio
import sys
from pathlib import Path

import aiohttp

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.utils.base_requester import BaseRequester


async def test_get_request():
    """Test a simple GET request."""
    print("Testing GET request...")
    async with aiohttp.ClientSession() as session:
        requester = BaseRequester(session, base_url="https://httpbin.org")
        response = await requester.get("/get", params={"param1": "value1", "param2": "value2"})
        print(f"GET response: {response}")
        assert response["args"] == {"param1": "value1", "param2": "value2"}
    print("GET request test passed!")


async def test_post_request():
    """Test a simple POST request with JSON data."""
    print("Testing POST request...")
    async with aiohttp.ClientSession() as session:
        requester = BaseRequester(session, base_url="https://httpbin.org")
        test_data = {"key1": "value1", "key2": "value2"}
        response = await requester.post("/post", json=test_data)
        print(f"POST response: {response}")
        assert response["json"] == test_data
    print("POST request test passed!")


async def test_custom_headers():
    """Test sending custom headers with a request."""
    print("Testing custom headers...")
    async with aiohttp.ClientSession() as session:
        requester = BaseRequester(session, base_url="https://httpbin.org")
        custom_headers = {"X-Custom-Header": "test-value"}
        response = await requester.get("/headers", headers=custom_headers)
        print(f"Headers response: {response}")
        assert "X-Custom-Header" in response["headers"]
        assert response["headers"]["X-Custom-Header"] == "test-value"
    print("Custom headers test passed!")


async def test_retry_logic():
    """Test the retry logic by requesting a URL that returns a 500 error."""
    print("Testing retry logic...")
    async with aiohttp.ClientSession() as session:
        requester = BaseRequester(
            session, 
            base_url="https://httpbin.org", 
            retries=2,
            backoff_factor=0.1
        )
        try:
            await requester.get("/status/500")
            print("This should not be reached as the request should fail")
            assert False
        except Exception as e:
            print(f"Expected error caught: {e}")
            assert "500" in str(e)
    print("Retry logic test passed!")


async def main():
    """Run all tests."""
    print("Starting BaseRequester tests...")
    
    try:
        await test_get_request()
        await test_post_request()
        await test_custom_headers()
        await test_retry_logic()
        
        print("\nAll tests passed successfully!")
    except Exception as e:
        print(f"\nTest failed: {e}")
        raise
    

if __name__ == "__main__":
    asyncio.run(main())