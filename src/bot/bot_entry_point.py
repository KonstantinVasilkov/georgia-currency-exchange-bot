"""
Main entrypoint for running the bot.
"""

import asyncio
from src.bot.bot import main

if __name__ == "__main__":
    asyncio.run(main())
