"""
Tests for bot initialization and setup.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand

from src.start_bot import setup_bot
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
    bot.set_my_commands = AsyncMock()
    return bot


@pytest.fixture
def mock_dispatcher() -> MagicMock:
    """
    Create a mock dispatcher instance.

    Returns:
        MagicMock: A mock dispatcher object.
    """
    dispatcher = MagicMock(spec=Dispatcher)
    return dispatcher


@pytest.mark.asyncio
async def test_setup_bot(mock_bot: MagicMock, mock_dispatcher: MagicMock) -> None:
    """
    Test bot setup and initialization.

    Args:
        mock_bot: Mock bot instance.
        mock_dispatcher: Mock dispatcher instance.
    """
    # Call the setup function
    await setup_bot(mock_bot, mock_dispatcher)

    # Verify that set_my_commands was called with the correct commands
    mock_bot.set_my_commands.assert_called_once()
    call_args = mock_bot.set_my_commands.call_args
    assert call_args is not None

    commands = call_args[0][0]
    assert isinstance(commands, list)
    assert len(commands) > 0

    # Verify that each command has the required attributes
    for command in commands:
        assert isinstance(command, BotCommand)
        assert command.command is not None
        assert command.description is not None


@pytest.mark.asyncio
async def test_setup_bot_error_handling(
    mock_bot: MagicMock, mock_dispatcher: MagicMock
) -> None:
    """
    Test error handling during bot setup.

    Args:
        mock_bot: Mock bot instance.
        mock_dispatcher: Mock dispatcher instance.
    """
    # Make set_my_commands raise an exception
    mock_bot.set_my_commands.side_effect = Exception("Test error")

    # Call the setup function and verify it handles the error
    with pytest.raises(Exception) as exc_info:
        await setup_bot(mock_bot, mock_dispatcher)

    assert str(exc_info.value) == "Test error"
