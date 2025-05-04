"""
Bot entrypoint module.

This module initializes and runs the Telegram bot using aiogram.
"""

import asyncio

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from src.config.logging_conf import get_logger
from src.config.settings import settings
from src.bot.routers import routers

logger = get_logger(__name__)


async def setup_bot(bot: Bot, dp: Dispatcher) -> None:
    """
    Set up bot commands and configuration.

    Args:
        bot: The bot instance to configure.
        dp: The dispatcher instance.
    """
    # Set up bot commands
    commands = [
        BotCommand(command="start", description="Start the bot"),
        BotCommand(command="help", description="Show help information"),
    ]
    await bot.set_my_commands(commands)


async def start_bot() -> None:
    """
    Start the bot with the configured settings.
    """
    try:
        # Initialize bot and dispatcher
        logger.info(f"Bot token: {settings.TELEGRAM_BOT_TOKEN}")
        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        storage = MemoryStorage()
        dp = Dispatcher(storage=storage)

        # Set up bot configuration
        await setup_bot(bot, dp)

        # Register routers
        for router in routers:
            dp.include_router(router)

        # Start polling
        logger.info("Starting bot...")
        await dp.start_polling(bot)

    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        raise
    finally:
        await bot.session.close()


def main() -> None:
    """
    Main entry point for the bot.
    """
    try:
        asyncio.run(start_bot())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped!")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise
