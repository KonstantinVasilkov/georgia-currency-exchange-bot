"""
Start command handler for the bot.
"""

from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from src.config.logging_conf import get_logger
from src.bot.keyboards.inline import get_main_menu_keyboard

logger = get_logger(__name__)

# Create router instance
router = Router(name="start_router")


@router.message(Command("start"))
async def handle_start(message: Message) -> None:
    """
    Handle the /start command.

    Args:
        message: The message.
    """
    if message.from_user:
        logger.info(f"User {message.from_user.id} started the bot")

    await message.answer(
        text="Welcome to the Currency Exchange Bot! Please select an option:",
        reply_markup=get_main_menu_keyboard(),
    )
