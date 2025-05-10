"""
Tests for bot functionality.
"""

import pytest
from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock

from aiogram.types import Message, User, Chat

from src.bot.routers.start import cmd_start
from src.config.logging_conf import get_logger

logger = get_logger(__name__)


@pytest.fixture
def mock_message() -> Any:
    """
    Create a mock message for testing.

    Returns:
        Any: A mock message object.
    """
    user = User(
        id=123456789,
        is_bot=False,
        first_name="Test",
        last_name="User",
        username="test_user",
        language_code="en",
    )
    chat = Chat(
        id=123456789,
        type="private",
        username="test_user",
        first_name="Test",
        last_name="User",
    )
    message = MagicMock(spec=Message)
    message.message_id = 1
    message.date = datetime.now()
    message.chat = chat
    message.from_user = user
    message.answer = AsyncMock()
    return message


@pytest.mark.asyncio
async def test_cmd_start(mock_message: Any) -> None:
    """
    Test the /start command handler.

    Args:
        mock_message: Mock message object.
    """
    # Call the command handler
    await cmd_start(mock_message)

    # Verify the answer was called with the correct text
    mock_message.answer.assert_called_once()
    call_args = mock_message.answer.call_args
    assert call_args is not None
    assert "Welcome to the Georgia Currency Exchange Bot" in call_args[0][0]
    assert "Use /help to see available commands" in call_args[0][0]


@pytest.mark.asyncio
async def test_cmd_start_without_user() -> None:
    """
    Test the /start command handler with a message without a user.
    """
    # Create a message without a user
    message = MagicMock(spec=Message)
    message.message_id = 1
    message.date = datetime.now()
    message.chat = Chat(id=123456789, type="private")
    message.from_user = None
    message.answer = AsyncMock()

    # Call the command handler
    await cmd_start(message)

    # Verify the answer was called
    message.answer.assert_called_once()
    call_args = message.answer.call_args
    assert call_args is not None
    assert "Welcome to the Georgia Currency Exchange Bot" in call_args[0][0]
