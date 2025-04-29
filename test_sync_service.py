"""
Simple test script to verify that the sync_exchange_data function works correctly.
"""

import asyncio
from src.services.SyncService import sync_exchange_data

async def main():
    """Run the sync_exchange_data function."""
    print("Testing sync_exchange_data function...")
    await sync_exchange_data()
    print("Test completed.")

if __name__ == "__main__":
    asyncio.run(main())