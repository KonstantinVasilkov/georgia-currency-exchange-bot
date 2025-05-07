"""Router for currency exchange functionality."""

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message

from src.bot.keyboards.inline import (
    get_main_menu_keyboard,
    get_currency_selection_keyboard,
    get_organization_keyboard,
    get_back_to_main_menu_keyboard,
)
from src.services.currency_service import CurrencyService, RateRow
from src.repositories.organization_repository import AsyncOrganizationRepository
from src.repositories.office_repository import AsyncOfficeRepository
from src.repositories.rate_repository import AsyncRateRepository
from src.config.logging_conf import get_logger
from sqlmodel.ext.asyncio.session import AsyncSession
from src.db.session import get_async_session, async_get_db_session
from src.db.models.rate import Rate
import asyncio

router = Router(name="currency_router")

# Available currencies - this should come from a service in the future
AVAILABLE_CURRENCIES = ["USD", "EUR", "GBP", "TRY", "RUB"]

logger = get_logger(__name__)


@router.callback_query(F.data == "best_rates_to_gel")
async def handle_best_rates_to_gel(callback: CallbackQuery) -> None:
    """
    Handle the best rates to GEL request by fetching real data from the database.
    Args:
        callback: The callback query.
    """
    # Dependency injection: create repositories and service
    async with async_get_db_session() as session:
        org_repo = AsyncOrganizationRepository(session=session)
        office_repo = AsyncOfficeRepository(session=session)
        rate_repo = AsyncRateRepository(session=session, model_class=Rate)
        service = CurrencyService(
            organization_repo=org_repo,
            office_repo=office_repo,
            rate_repo=rate_repo,
        )
        try:
            rows = await service.get_latest_rates_table()
        except Exception as exc:
            logger.warning(f"Failed to fetch rates: {exc}")
            rows = []
    # Format as pretty table in monospace (Telegram code block)
    if not rows:
        response = "No rates available."
    else:
        # Prepare pretty table (single line per org)
        header = f"{'🏦 Organization':<22} │ {'🇺🇸 USD':>8} │ {'🇪🇺 EUR':>8} │ {'🇷🇺 RUB':>8}"
        sep = "─" * len(header)
        lines = [header, sep]
        for row in rows:
            org = row.organization if row.organization else '-'
            usd = f"{row.usd:.4f}" if row.usd is not None else '-'
            eur = f"{row.eur:.4f}" if row.eur is not None else '-'
            rub = f"{row.rub:.5f}" if row.rub is not None else '-'
            lines.append(f"{org:<22} │ {usd:>8} │ {eur:>8} │ {rub:>8}")
        table = '\n'.join(lines)
        response = (
            "<b>💱 Latest Exchange Rates to GEL</b>\n"
            "<i>1. National Bank of Georgia (NBG)</i>\n"
            "<i>2-4. Online Banks</i>\n"
            "<i>5-10. Best Other Organizations</i>\n\n"
            f"<pre>{table}</pre>"
        )
    if callback.message is not None and isinstance(callback.message, Message):
        await callback.message.edit_text(
            text=response, reply_markup=get_back_to_main_menu_keyboard(), parse_mode="HTML"
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
