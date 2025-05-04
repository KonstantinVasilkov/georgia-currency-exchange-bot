"""
Start command handler for the bot.
"""

from aiogram import Router, types
from aiogram.filters import Command

from src.config.logging_conf import get_logger

logger = get_logger(__name__)

# Create router instance
router = Router()


@router.message(Command("start"))
async def cmd_start(message: types.Message) -> None:
    """
    Handle the /start command.

    Args:
        message: The message object from Telegram.
    """
    if message.from_user:
        logger.info(f"User {message.from_user.id} started the bot")

    welcome_text = (
        "👋 Welcome to the Georgia Currency Exchange Bot!\n\n"
        "I can help you find the best currency exchange rates in Georgia.\n"
        "Use /help to see available commands."
    )

    await message.answer(welcome_text)
