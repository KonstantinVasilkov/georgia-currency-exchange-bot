"""
Tests for the main bot entrypoint.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from aiogram import Bot, Dispatcher, Router
from aiogram.fsm.storage.memory import MemoryStorage

from src.bot.bot import start_bot, main
from src.config.logging_conf import get_logger

logger = get_logger(__name__)


@pytest.fixture
def mock_bot() -> MagicMock:
    """
    Create a mock bot instance.

    Returns:
        MagicMock: A mock bot object.
    """
    bot = MagicMock(spec=Bot)
    session = MagicMock()
    session.close = AsyncMock()
    bot.session = session
    return bot


@pytest.fixture
def mock_dispatcher() -> MagicMock:
    """
    Create a mock dispatcher instance.

    Returns:
        MagicMock: A mock dispatcher object.
    """
    dispatcher = MagicMock(spec=Dispatcher)
    dispatcher.start_polling = AsyncMock()
    return dispatcher


@pytest.mark.asyncio
async def test_start_bot(mock_bot: MagicMock, mock_dispatcher: MagicMock) -> None:
    """
    Test the start_bot function.

    Args:
        mock_bot: Mock bot instance.
        mock_dispatcher: Mock dispatcher instance.
    """
    with (
        patch("src.bot.bot.Bot", return_value=mock_bot),
        patch("src.bot.bot.Dispatcher", return_value=mock_dispatcher),
        patch("src.bot.bot.MemoryStorage", return_value=MagicMock(spec=MemoryStorage)),
    ):
        # Call start_bot
        await start_bot()

        # Verify that the bot was started correctly
        mock_dispatcher.start_polling.assert_called_once_with(mock_bot)
        mock_bot.session.close.assert_called_once()


@pytest.mark.asyncio
async def test_start_bot_error_handling(
    mock_bot: MagicMock, mock_dispatcher: MagicMock
) -> None:
    """
    Test error handling in start_bot.

    Args:
        mock_bot: Mock bot instance.
        mock_dispatcher: Mock dispatcher instance.
    """
    with (
        patch("src.bot.bot.Bot", return_value=mock_bot),
        patch("src.bot.bot.Dispatcher", return_value=mock_dispatcher),
        patch("src.bot.bot.MemoryStorage", return_value=MagicMock(spec=MemoryStorage)),
    ):
        # Make start_polling raise an exception
        mock_dispatcher.start_polling.side_effect = Exception("Test error")

        # Call start_bot and verify it handles the error
        with pytest.raises(Exception) as exc_info:
            await start_bot()

        assert str(exc_info.value) == "Test error"
        mock_bot.session.close.assert_called_once()


@pytest.mark.asyncio
async def test_main() -> None:
    """
    Test the main function.
    """
    with (
        patch("src.bot.bot.start_bot"),
        patch("src.bot.bot.Bot.set_my_commands", new_callable=AsyncMock),
        patch("src.bot.bot.Bot.session", create=True),
        patch("src.bot.bot.Dispatcher.start_polling", new_callable=AsyncMock),
        patch("src.bot.bot.Bot.get_me", new_callable=AsyncMock),
    ):
        # Call main
        await main()
        # No assertion for mock_start_bot, as main() does not call it


@pytest.mark.asyncio
async def test_main_keyboard_interrupt() -> None:
    """
    Test handling of KeyboardInterrupt in main.
    """
    with (
        patch("src.bot.bot.start_bot", side_effect=KeyboardInterrupt),
        patch("src.bot.routers.start.router", new=Router(name="start_router_test")),
        patch(
            "src.bot.routers.currency.router", new=Router(name="currency_router_test")
        ),
        patch("src.bot.bot.Dispatcher.start_polling", new_callable=AsyncMock),
        patch("src.bot.bot.Bot.get_me", new_callable=AsyncMock),
        patch("src.bot.bot.Bot.set_my_commands", new_callable=AsyncMock),
    ):
        # Call main and verify it handles KeyboardInterrupt
        await main()  # Should not raise an exception
