"""
Conversion router for currency pair conversion flows.

Handles best rates between currencies and currency pair selection.
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from src.bot.keyboards.inline import (
    get_currency_selection_keyboard,
    get_back_to_main_menu_keyboard,
)
from src.config.logging_conf import get_logger

router = Router(name="conversion_router")
logger = get_logger(__name__)

AVAILABLE_CURRENCIES = ["USD", "EUR", "GBP", "TRY", "RUB"]


@router.callback_query(F.data == "best_rates_between")
async def handle_best_rates_between(callback: CallbackQuery) -> None:
    """
    Handle the best rates between currencies request.
    """
    if callback.message is not None and isinstance(callback.message, Message):
        await callback.message.edit_text(
            text="Select first currency:",
            reply_markup=get_currency_selection_keyboard(
                currencies=AVAILABLE_CURRENCIES, callback_prefix="from_currency"
            ),
        )


@router.callback_query(F.data.startswith("from_currency:"))
async def handle_from_currency_selection(callback: CallbackQuery) -> None:
    """
    Handle the first currency selection for conversion.
    """
    from_currency = callback.data.split(":")[1] if callback.data else ""
    if callback.message is not None and isinstance(callback.message, Message):
        await callback.message.edit_text(
            text=f"Selected {from_currency}. Now select second currency:",
            reply_markup=get_currency_selection_keyboard(
                currencies=[c for c in AVAILABLE_CURRENCIES if c != from_currency],
                callback_prefix="to_currency",
            ),
        )


@router.callback_query(F.data.startswith("to_currency:"))
async def handle_to_currency_selection(callback: CallbackQuery) -> None:
    """
    Handle the second currency selection and show rates (stub).
    """
    # TODO: Implement actual rate fetching from CurrencyService
    rates = [
        "1 USD = 0.93 EUR (Bank of Georgia)",
        "1 USD = 0.79 GBP (TBC Bank)",
        "1 USD = 31.18 TRY (Liberty Bank)",
        "1 USD = 91.38 RUB (ProCredit Bank)",
    ]
    response = "Top 5 best rates between currencies:\n\n" + "\n".join(rates)
    if callback.message is not None and isinstance(callback.message, Message):
        await callback.message.edit_text(
            text=response, reply_markup=get_back_to_main_menu_keyboard()
        )
