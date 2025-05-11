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
from src.services.currency_service import CurrencyService
from src.repositories.organization_repository import AsyncOrganizationRepository
from src.repositories.office_repository import AsyncOfficeRepository
from src.repositories.rate_repository import AsyncRateRepository
from src.db.session import async_get_db_session
from src.db.models.rate import Rate

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
    Handle the second currency selection and show real best rates between currencies.
    """
    # Parse from_currency from previous message or context
    from_currency = None
    if callback.message and callback.message.text:
        import re
        match = re.match(r"Selected (\w+). Now select second currency:", callback.message.text)
        if match:
            from_currency = match.group(1)
    if not from_currency:
        from_currency = "USD"  # fallback
    to_currency = callback.data.split(":")[1] if callback.data else ""
    # Fetch best rates for the selected pair
    async with async_get_db_session() as session:
        org_repo = AsyncOrganizationRepository(session=session)
        office_repo = AsyncOfficeRepository(session=session)
        rate_repo = AsyncRateRepository(session=session, model_class=Rate)
        service = CurrencyService(org_repo, office_repo, rate_repo)
        rates = await service.get_best_rates_for_pair(
            sell_currency=from_currency, get_currency=to_currency
        )
    if not rates:
        response = f"No rates available for {from_currency} → {to_currency}."
    else:
        name_width = 15
        header = f"{from_currency} → {to_currency}\n{'Organization':<{name_width}} | {'Rate':>10}"
        sep = "─" * (name_width + 3 + 10)
        lines = [header, sep]
        for r in rates:
            org = r["organization"]
            rate_str = f"{r['rate']:.4f}"
            lines.append(f"{org:<{name_width}} | {rate_str:>10}")
        response = "\n".join(lines)
    if callback.message is not None and isinstance(callback.message, Message):
        await callback.message.edit_text(
            text=response, reply_markup=get_back_to_main_menu_keyboard()
        )
