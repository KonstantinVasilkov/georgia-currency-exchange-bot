"""
Rates router for currency exchange rate queries.

Handles best rates, rate tables, and organization office listings.
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from src.bot.keyboards.inline import (
    get_main_menu_keyboard,
    get_currency_selection_keyboard,
)
from src.services.currency_service import CurrencyService
from src.repositories.organization_repository import AsyncOrganizationRepository
from src.repositories.office_repository import AsyncOfficeRepository
from src.repositories.rate_repository import AsyncRateRepository
from src.config.logging_conf import get_logger
from src.db.session import async_get_db_session
from src.db.models.rate import Rate

router = Router(name="rates_router")
logger = get_logger(__name__)

AVAILABLE_CURRENCIES = ["USD", "EUR", "GBP", "TRY", "RUB"]
AVAILABLE_BOT_CURRENCIES = ["USD", "EUR", "GBP", "RUB", "GEL"]


@router.callback_query(F.data == "best_rates")
async def handle_best_rates(callback: CallbackQuery) -> None:
    """
    Start the best rates flow: ask which currency the user wants to sell.
    """
    if callback.message is not None and isinstance(callback.message, Message):
        await callback.message.edit_text(
            text="Which currency do you want to sell?",
            reply_markup=get_currency_selection_keyboard(
                currencies=AVAILABLE_BOT_CURRENCIES, callback_prefix="sell_currency"
            ),
        )


@router.callback_query(F.data == "main_menu")
async def handle_main_menu(callback: CallbackQuery) -> None:
    """
    Handle the main menu request and show the latest rates table.
    """
    if callback.message is not None and isinstance(callback.message, Message):
        async with async_get_db_session() as session:
            org_repo = AsyncOrganizationRepository(session=session)
            office_repo = AsyncOfficeRepository(session=session)
            rate_repo = AsyncRateRepository(session=session, model_class=Rate)
            service = CurrencyService(
                organization_repo=org_repo,
                office_repo=office_repo,
                rate_repo=rate_repo,
            )
            rows = await service.get_latest_rates_table()

        name_width = 15
        header = (
            f"{'Organization':<{name_width}} | {'USD':>7} | {'EUR':>7} | {'RUB':>7}"
        )
        sep = "─" * (name_width + 3 + 9 + 3 + 9 + 3 + 9)
        lines = [header, sep]
        for row in rows[:4]:
            org = row.organization
            usd = f"{row.usd:.4f}" if row.usd is not None else "-"
            eur = f"{row.eur:.4f}" if row.eur is not None else "-"
            rub = f"{row.rub:.4f}" if row.rub is not None else "-"
            lines.append(f"{org:<{name_width}} | {usd:>7} | {eur:>7} | {rub:>7}")
        table_str = "\n".join(lines)

        from datetime import datetime, UTC, timedelta

        latest_ts = datetime.now(UTC)
        gmt4_offset = timedelta(hours=4)
        latest_ts_gmt4 = latest_ts.astimezone(UTC) + gmt4_offset
        last_update_str = latest_ts_gmt4.strftime("%Y-%m-%d %H:%M") + " (GMT+4)"

        welcome = f"Welcome to the Currency Exchange Bot!\nLatest rates for the {last_update_str}:"
        prompt = "\nPlease select an option:"
        await callback.message.edit_text(
            text=f"{welcome}\n<pre>{table_str}</pre>{prompt}",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="HTML",
        )
