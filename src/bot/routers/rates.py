"""
Rates router for currency exchange rate queries.

Handles best rates, rate tables, and organization office listings.
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from src.bot.keyboards.inline import (
    get_main_menu_keyboard,
    get_currency_selection_keyboard,
    get_back_to_main_menu_keyboard,
)
from src.services.currency_service import CurrencyService
from src.repositories.organization_repository import AsyncOrganizationRepository
from src.repositories.office_repository import AsyncOfficeRepository
from src.repositories.rate_repository import AsyncRateRepository
from src.config.logging_conf import get_logger
from src.db.session import async_get_db_session
from src.db.models.rate import Rate
from src.bot.utils.logging_decorator import log_router_call

router = Router(name="rates_router")
logger = get_logger(__name__)

AVAILABLE_CURRENCIES = ["USD", "EUR", "GBP", "TRY", "RUB"]
AVAILABLE_BOT_CURRENCIES = ["USD", "EUR", "GBP", "RUB", "GEL"]


@router.callback_query(F.data == "best_rates")
@log_router_call
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
@log_router_call
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


@router.callback_query(F.data.startswith("sell_currency:"))
@log_router_call
async def handle_sell_currency_selection(callback: CallbackQuery) -> None:
    """
    Handle sell currency selection for best rates, then ask for get currency.
    """
    sell_currency = callback.data.split(":")[1] if callback.data else ""
    options = [c for c in AVAILABLE_BOT_CURRENCIES if c != sell_currency]
    if callback.message is not None and isinstance(callback.message, Message):
        await callback.message.edit_text(
            text=f"Selected {sell_currency}. What currency do you want to get?",
            reply_markup=get_currency_selection_keyboard(
                currencies=options,
                callback_prefix="get_currency",
            ),
        )


@router.callback_query(F.data.startswith("get_currency:"))
@log_router_call
async def handle_get_currency_selection(callback: CallbackQuery) -> None:
    """
    Handle get currency selection and show best rates for the selected pair, with exact previous formatting.
    """
    import re
    from datetime import datetime, UTC, timedelta

    get_currency = callback.data.split(":")[1] if callback.data else ""
    # Try to extract the sell currency from the previous message text
    sell_currency = None
    if isinstance(callback.message, Message) and callback.message.text:
        match = re.match(
            r"Selected (\w+). What currency do you want to get?", callback.message.text
        )
        if match:
            sell_currency = match.group(1)
    if not sell_currency:
        sell_currency = "USD"  # fallback for now

    # Fetch best rates for the selected pair
    async with async_get_db_session() as session:
        org_repo = AsyncOrganizationRepository(session=session)
        office_repo = AsyncOfficeRepository(session=session)
        rate_repo = AsyncRateRepository(session=session, model_class=Rate)
        service = CurrencyService(
            organization_repo=org_repo,
            office_repo=office_repo,
            rate_repo=rate_repo,
        )
        rates = await service.get_best_rates_for_pair(
            sell_currency=sell_currency, get_currency=get_currency
        )

    # Collect timestamps for all rates (if available)
    timestamps = []
    async with async_get_db_session() as session:
        office_repo = AsyncOfficeRepository(session=session)
        rate_repo = AsyncRateRepository(session=session, model_class=Rate)
        for r in rates:
            org_name_obj = r["organization"]
            org_name_str = (
                str(org_name_obj) if not isinstance(org_name_obj, str) else org_name_obj
            )
            org = await org_repo.find_one_by(name=org_name_str)
            if not org:
                continue
            offices = await office_repo.get_by_organization(org.id)
            if not offices:
                continue
            office = offices[0]
            # Find the rate for the sell_currency (buy) or get_currency (sell)
            rate_objs = await rate_repo.get_rates_by_office(office.id, limit=10)
            for rate_obj in rate_objs:
                if (
                    rate_obj.currency == sell_currency
                    or rate_obj.currency == get_currency
                ):
                    if hasattr(rate_obj, "timestamp") and rate_obj.timestamp:
                        timestamps.append(rate_obj.timestamp)

    latest_ts = max(timestamps) if timestamps else None
    now_utc = datetime.now(UTC)
    outdated = False
    if latest_ts:
        # Ensure latest_ts is timezone-aware (assume UTC if naive)
        if latest_ts.tzinfo is None or latest_ts.tzinfo.utcoffset(latest_ts) is None:
            latest_ts = latest_ts.replace(tzinfo=UTC)
        if (now_utc - latest_ts).total_seconds() > 3 * 3600:
            outdated = True
    # Format timestamp for display
    if latest_ts:
        # Convert to GMT+4
        gmt4_offset = timedelta(hours=4)
        latest_ts_gmt4 = latest_ts.astimezone(UTC) + gmt4_offset
        last_update_str = latest_ts_gmt4.strftime("%Y-%m-%d %H:%M") + " (GMT+4)"
    else:
        if isinstance(callback.message, Message):
            await callback.message.edit_text(
                text=f"No rates available for {sell_currency} → {get_currency}.",
                reply_markup=get_back_to_main_menu_keyboard(),
            )
        return

    # Emoji map for currencies
    currency_emoji = {
        "USD": "🇺🇸",
        "EUR": "🇪🇺",
        "GBP": "🇬🇧",
        "RUB": "🇷🇺",
        "GEL": "🇬🇪",
    }
    pair_emoji = f"{currency_emoji.get(sell_currency, sell_currency)} → {currency_emoji.get(get_currency, get_currency)}"

    # Org name mapping for online banks and NBG
    org_name_map = {
        "mBank": "BoG[online]",
        "TBC mobile": "TBC[online]",
        "MyCredo": "Credo[online]",
        "National Bank of Georgia": "NBG[official]",
        "NBG": "NBG[official]",
    }

    def trim_name(name: str, width: int = 15) -> str:
        return name if len(name) <= width else name[: width - 1] + "…"

    if not rates:
        if isinstance(callback.message, Message):
            await callback.message.edit_text(
                text=f"No rates available for {sell_currency} → {get_currency}.",
                reply_markup=get_back_to_main_menu_keyboard(),
            )
        return
    else:
        # Table header
        name_width = 15
        header = f"{pair_emoji}\n{'Organization':<{name_width}} | {'Rate':>10}"
        sep = "─" * (name_width + 3 + 10)
        lines = [header, sep]
        # NBG row (always first if present)
        nbg_row = None
        online_rows = []
        other_rows = []
        for r in rates:
            org_name_obj = r["organization"]
            org_name_str = (
                str(org_name_obj) if not isinstance(org_name_obj, str) else org_name_obj
            )
            display_org = org_name_map.get(org_name_str, org_name_str)
            display_org = trim_name(display_org, name_width)
            rate_str = f"{r['rate']:.4f}"
            if display_org == "NBG[official]":
                nbg_row = f"{display_org:<{name_width}} | {rate_str:>10}"
            elif (
                display_org in org_name_map.values() and display_org != "NBG[official]"
            ):
                online_rows.append(f"{display_org:<{name_width}} | {rate_str:>10}")
            else:
                other_rows.append(f"{display_org:<{name_width}} | {rate_str:>10}")
        if nbg_row:
            lines.append(nbg_row)
            lines.append(sep)
        if online_rows:
            lines.extend(online_rows)
            lines.append(sep)
        if other_rows:
            lines.extend(other_rows)
        table_str = "\n".join(lines)
        # Add last update info
        last_update_line = f"Last rate update: {last_update_str}"
        # Add warning if outdated
        warning = ""
        if outdated:
            warning = "<b>\u26a0\ufe0f Rates may be outdated! Please recheck on [myfin.ge](https://myfin.ge/)</b>\n"
        response = f"{warning}<pre>{table_str}\n{last_update_line}</pre>"

    if isinstance(callback.message, Message):
        await callback.message.edit_text(
            text=response,
            reply_markup=get_back_to_main_menu_keyboard(),
            parse_mode="HTML",
        )
