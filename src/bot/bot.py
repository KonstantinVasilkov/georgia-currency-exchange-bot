"""
Bot entrypoint module.

This module initializes and runs the Telegram bot using aiogram.
"""

import asyncio
import logging
from typing import Sequence

from aiogram import Bot, Dispatcher, Router
from aiogram.enums import ParseMode
from aiogram.types import BotCommand
from aiogram.fsm.storage.memory import MemoryStorage

from src.config.logging_conf import get_logger
from src.config.settings import settings
from src.bot.routers import start, currency

logger = get_logger(__name__)


async def set_commands(bot: Bot) -> None:
    """
    Set bot commands.

    Args:
        bot: The bot instance.
    """
    commands = [
        BotCommand(command="start", description="Start the bot"),
    ]
    await bot.set_my_commands(commands)


async def setup_bot(bot: Bot, dispatcher: Dispatcher) -> None:
    """Set up bot commands and register routers. Used for test compatibility."""
    try:
        commands = [
            BotCommand(command="start", description="Start the bot"),
        ]
        await bot.set_my_commands(commands)
        dispatcher.include_router(start.router)
        dispatcher.include_router(currency.router)
    except Exception as exc:
        logger.error(f"Error in setup_bot: {exc}")
        raise


async def start_bot() -> None:
    """Start the bot for test compatibility. Initializes and runs the bot with routers."""
    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN, parse_mode=ParseMode.HTML)
    storage = MemoryStorage()
    dispatcher = Dispatcher(storage=storage)
    await setup_bot(bot, dispatcher)
    try:
        await dispatcher.start_polling(bot)
    finally:
        await bot.session.close()


async def main() -> None:
    """
    Run the bot.
    """
    try:
        # Initialize bot and dispatcher
        logger.info(f"Bot token: {settings.TELEGRAM_BOT_TOKEN}")
        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN, parse_mode=ParseMode.HTML)
        dp = Dispatcher()

        # Register routers
        routers: Sequence[Router] = (
            start.router,
            currency.router,
        )
        for router in routers:
            dp.include_router(router)

        # Set bot commands
        await set_commands(bot)

        # Start polling
        logger.info("Starting bot...")
        await dp.start_polling(bot)

    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        raise
    finally:
        await bot.session.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
