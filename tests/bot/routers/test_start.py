import pytest
from aiogram.types import Message
from unittest.mock import AsyncMock, patch
from src.bot.routers.start import handle_start


class DummyAsyncSession:
    async def __aenter__(self):
        return AsyncMock()

    async def __aexit__(self, exc_type, exc, tb):
        pass


@pytest.mark.asyncio
async def test_handle_start_sends_welcome_table_message():
    # Mock message
    message = AsyncMock(spec=Message)
    message.from_user = AsyncMock()
    message.from_user.id = 123
    message.answer = AsyncMock()

    # Patch CurrencyService.get_latest_rates_table to return a fixed table
    fake_rows = [
        # NBG row
        type("Row", (), {"organization": "NBG", "usd": 2.5, "eur": 2.7, "rub": 0.03})(),
        # Online banks
        type(
            "Row",
            (),
            {"organization": "BoG[online]", "usd": 2.51, "eur": 2.71, "rub": 0.031},
        )(),
        type(
            "Row",
            (),
            {"organization": "TBC[online]", "usd": 2.52, "eur": 2.72, "rub": 0.032},
        )(),
        type(
            "Row",
            (),
            {"organization": "Credo[online]", "usd": 2.53, "eur": 2.73, "rub": 0.033},
        )(),
    ]
    with patch(
        "src.bot.routers.start.CurrencyService.get_latest_rates_table",
        new=AsyncMock(return_value=fake_rows),
    ):
        with (
            patch("src.bot.routers.start.AsyncOrganizationRepository"),
            patch("src.bot.routers.start.AsyncOfficeRepository"),
            patch("src.bot.routers.start.AsyncRateRepository"),
            patch("src.bot.routers.start.async_get_db_session", DummyAsyncSession),
        ):
            await handle_start(message)

    # Check that message.answer was called with the expected table and prompt
    called_args = message.answer.call_args[1]
    assert "Organization" in called_args["text"]
    assert "NBG" in called_args["text"]
    assert "BoG[online]" in called_args["text"]
    assert "Welcome to the Currency Exchange Bot!" in called_args["text"]
    assert "Please select an option" in called_args["text"]
    assert called_args["parse_mode"] == "HTML"
