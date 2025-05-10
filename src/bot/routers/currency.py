"""Router for currency exchange functionality."""

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message

from src.bot.keyboards.inline import (
    get_main_menu_keyboard,
    get_currency_selection_keyboard,
    get_organization_keyboard,
    get_back_to_main_menu_keyboard,
)
from src.services.currency_service import CurrencyService
from src.repositories.organization_repository import AsyncOrganizationRepository
from src.repositories.office_repository import AsyncOfficeRepository
from src.repositories.rate_repository import AsyncRateRepository
from src.config.logging_conf import get_logger
from src.db.session import async_get_db_session
from src.db.models.rate import Rate

router = Router(name="currency_router")

# Available currencies - this should come from a service in the future
AVAILABLE_CURRENCIES = ["USD", "EUR", "GBP", "TRY", "RUB"]

# New available currencies including 'GEL'
AVAILABLE_BOT_CURRENCIES = ["USD", "EUR", "GBP", "RUB", "GEL"]

logger = get_logger(__name__)


@router.callback_query(F.data == "best_rates")
async def handle_best_rates(callback: CallbackQuery) -> None:
    """
    Start the best rates flow: ask which currency the user wants to sell.
    """
    if callback.message is not None and isinstance(callback.message, Message):
        await callback.message.edit_text(
            text="Which currency do you want to sell?",
            reply_markup=get_currency_selection_keyboard(
                currencies=AVAILABLE_BOT_CURRENCIES,
                callback_prefix="sell_currency"
            ),
        )


@router.callback_query(F.data == "best_rates_between")
async def handle_best_rates_between(callback: CallbackQuery) -> None:
    """Handle the best rates between currencies request.

    Args:
        callback: The callback query.
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
    """Handle the first currency selection.

    Args:
        callback: The callback query.
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
    """Handle the second currency selection and show rates.

    Args:
        callback: The callback query.
    """
    # TODO: Implement actual rate fetching from CurrencyService
    to_currency = callback.data.split(":")[1] if callback.data else ""  # noqa
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


@router.callback_query(F.data == "list_organizations")
async def handle_list_organizations(callback: CallbackQuery) -> None:
    """Handle the list organizations request.

    Args:
        callback: The callback query.
    """
    # TODO: Implement actual organization fetching from OrganizationService
    organizations = [
        "Bank of Georgia",
        "TBC Bank",
        "Liberty Bank",
        "ProCredit Bank",
        "Basis Bank",
    ]

    if callback.message is not None and isinstance(callback.message, Message):
        await callback.message.edit_text(
            text="Select an organization to view its offices:",
            reply_markup=get_organization_keyboard(organizations=organizations),
        )


@router.callback_query(F.data.startswith("org:"))
async def handle_organization_selection(callback: CallbackQuery) -> None:
    """Handle the organization selection and show its offices.

    Args:
        callback: The callback query.
    """
    # TODO: Implement actual office fetching from OrganizationService
    org_name = callback.data.split(":")[1] if callback.data else ""
    offices = [
        "Main Branch - Rustaveli Ave. 7",
        "Vake Branch - Chavchavadze Ave. 60",
        "Saburtalo Branch - Pekini Ave. 45",
        "Didube Branch - Agmashenebeli Ave. 120",
    ]

    response = f"Offices of {org_name}:\n\n" + "\n".join(offices)
    if callback.message is not None and isinstance(callback.message, Message):
        await callback.message.edit_text(
            text=response, reply_markup=get_back_to_main_menu_keyboard()
        )


@router.callback_query(F.data == "main_menu")
async def handle_main_menu(callback: CallbackQuery) -> None:
    """Handle the main menu request.

    Args:
        callback: The callback query.
    """
    if callback.message is not None and isinstance(callback.message, Message):
        await callback.message.edit_text(
            text="Welcome to the Currency Exchange Bot! Please select an option:",
            reply_markup=get_main_menu_keyboard(),
        )


@router.callback_query(F.data.startswith("sell_currency:"))
async def handle_sell_currency_selection(callback: CallbackQuery) -> None:
    """
    Handle the sell currency selection and ask for the currency to get.
    """
    sell_currency = callback.data.split(":")[1] if callback.data else ""
    options = [c for c in AVAILABLE_BOT_CURRENCIES if c != sell_currency]
    if callback.message is not None and isinstance(callback.message, Message):
        await callback.message.edit_text(
            text=f"Selected {sell_currency}. What currency do you want to get?",
            reply_markup=get_currency_selection_keyboard(
                currencies=options,
                callback_prefix="get_currency"
            ),
        )


@router.callback_query(F.data.startswith("get_currency:"))
async def handle_get_currency_selection(callback: CallbackQuery) -> None:
    """
    Handle the get currency selection and show best rates.
    """
    get_currency = callback.data.split(":")[1] if callback.data else ""
    # Try to extract the sell currency from the previous message text
    sell_currency = None
    if callback.message and callback.message.text:
        # Message text is like: 'Selected USD. What currency do you want to get?'
        import re
        match = re.match(r"Selected (\w+). What currency do you want to get\?", callback.message.text)
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
        rates = await service.get_best_rates_for_pair(sell_currency=sell_currency, get_currency=get_currency)

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
        return name if len(name) <= width else name[:width-1] + '…'

    if not rates:
        response = f"No rates available for {sell_currency} → {get_currency}."
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
            org = r['organization']
            display_org = org_name_map.get(org, org)
            display_org = trim_name(display_org, name_width)
            rate_str = f"{r['rate']:.4f}"
            if display_org == "NBG[official]":
                nbg_row = f"{display_org:<{name_width}} | {rate_str:>10}"
            elif display_org in org_name_map.values() and display_org != "NBG[official]":
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
        table_str = '\n'.join(lines)
        response = f"<pre>{table_str}</pre>"

    if callback.message is not None and isinstance(callback.message, Message):
        await callback.message.edit_text(
            text=response,
            reply_markup=get_back_to_main_menu_keyboard(),
            parse_mode="HTML",
        )
