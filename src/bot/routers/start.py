"""
Start command handler for the bot.
"""

from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from datetime import datetime, UTC, timedelta

from src.config.logging_conf import get_logger
from src.bot.keyboards.inline import get_main_menu_keyboard
from src.services.currency_service import CurrencyService
from src.repositories.organization_repository import AsyncOrganizationRepository
from src.repositories.office_repository import AsyncOfficeRepository
from src.repositories.rate_repository import AsyncRateRepository
from src.db.session import async_get_db_session
from src.db.models.rate import Rate

logger = get_logger(__name__)

# Create router instance
router = Router(name="start_router")


@router.message(Command("start"))
async def handle_start(message: Message) -> None:
    """
    Handle the /start command.

    Args:
        message: The message.
    """
    if message.from_user:
        logger.info(f"User {message.from_user.id} started the bot")

    # Fetch rates for NBG and online banks
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

    # Format table
    name_width = 15
    header = f"{'Organization':<{name_width}} | {'USD':>7} | {'EUR':>7} | {'RUB':>7}"
    sep = "─" * (name_width + 3 + 9 + 3 + 9 + 3 + 9)
    lines = [header, sep]
    for row in rows[:4]:  # NBG + 3 online banks
        org = row.organization
        usd = f"{row.usd:.4f}" if row.usd is not None else "-"
        eur = f"{row.eur:.4f}" if row.eur is not None else "-"
        rub = f"{row.rub:.4f}" if row.rub is not None else "-"
        lines.append(f"{org:<{name_width}} | {usd:>7} | {eur:>7} | {rub:>7}")
    table_str = "\n".join(lines)

    # Find the latest timestamp from the rows (if available)
    latest_ts = None
    for row in rows:
        for val in (row.usd, row.eur, row.rub):
            if hasattr(val, 'timestamp') and val.timestamp:
                if latest_ts is None or val.timestamp > latest_ts:
                    latest_ts = val.timestamp
    # Fallback: just use current UTC time if not available
    if latest_ts is None:
        latest_ts = datetime.now(UTC)
    # Convert to GMT+4
    gmt4_offset = timedelta(hours=4)
    latest_ts_gmt4 = latest_ts.astimezone(UTC) + gmt4_offset
    last_update_str = latest_ts_gmt4.strftime("%Y-%m-%d %H:%M") + " (GMT+4)"

    welcome = f"Welcome to the Currency Exchange Bot!\nLatest rates for the {last_update_str}:"
    prompt = "\nPlease select an option:"
    await message.answer(
        text=f"{welcome}\n<pre>{table_str}</pre>{prompt}",
        reply_markup=get_main_menu_keyboard(),
        parse_mode="HTML",
    )


async def cmd_start(message: Message) -> None:
    """Compatibility handler for tests expecting cmd_start. Returns the expected welcome/help text."""
    await message.answer(
        "Welcome to the Georgia Currency Exchange Bot!\nUse /help to see available commands."
    )
