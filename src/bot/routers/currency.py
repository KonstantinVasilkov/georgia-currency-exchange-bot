"""Router for currency exchange functionality."""

from aiogram import Router, F
from aiogram.types import (
    CallbackQuery,
    Message,
    Message as AiogramMessage,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from datetime import datetime, UTC, timedelta
from math import radians, cos, sin, sqrt, atan2
from typing import Any, Sequence

from src.bot.keyboards.inline import (
    get_main_menu_keyboard,
    get_currency_selection_keyboard,
    get_organization_keyboard,
    get_back_to_main_menu_keyboard,
    get_find_office_menu_keyboard,
    get_location_or_fallback_keyboard,
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

# Simple in-memory state for demo (user_id -> context)
user_search_state: dict[int, dict[str, Any]] = {}


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two points (km)."""
    R = 6371.0  # Earth radius in km
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = (
        sin(dlat / 2) ** 2
        + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    )
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c


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


def generate_google_maps_multi_pin_url(offices: Sequence[Any]) -> str:
    """Generate a Google Maps URL with multiple pins for the given offices."""
    if not offices:
        return "https://maps.google.com/"
    base = "https://www.google.com/maps/dir/"
    waypoints = "/".join(f"{o.lat:.4f},{o.lng:.4f}" for o in offices)
    return f"{base}{waypoints}"


def generate_apple_maps_multi_pin_url(offices: Sequence[Any]) -> str:
    """Generate an Apple Maps URL with multiple pins for the given offices."""
    if not offices:
        return "http://maps.apple.com/"
    pins = "&".join(f"q={o.lat:.4f},{o.lng:.4f}" for o in offices)
    return f"http://maps.apple.com/?{pins}"


@router.callback_query(F.data.startswith("org:"))
async def handle_organization_selection(callback: CallbackQuery) -> None:
    """
    Handle the organization selection and show its offices with map links.
    """
    org_name = callback.data.split(":")[1] if callback.data else ""
    async with async_get_db_session() as session:
        org_repo = AsyncOrganizationRepository(session=session)
        office_repo = AsyncOfficeRepository(session=session)
        org = await org_repo.find_one_by(name=org_name)
        if not org:
            if callback.message is not None and hasattr(callback.message, "edit_text"):
                await callback.message.edit_text(
                    text=f"Organization '{org_name}' not found.",
                    reply_markup=get_back_to_main_menu_keyboard(),
                )
            return
        offices: Sequence[Any] = await office_repo.get_by_organization(org.id)
        if not offices:
            if callback.message is not None and hasattr(callback.message, "edit_text"):
                await callback.message.edit_text(
                    text=f"No offices found for {org_name}.",
                    reply_markup=get_back_to_main_menu_keyboard(),
                )
            return
        office_lines = [f"{o.name} - {o.address}" for o in offices]
        gmaps_url = generate_google_maps_multi_pin_url(offices)
        amap_url = generate_apple_maps_multi_pin_url(offices)
        response = (
            f"Offices of <b>{org_name}</b>:\n\n"
            + "\n".join(office_lines)
            + f"\n\n<a href='{gmaps_url}'>Open all in Google Maps</a> | <a href='{amap_url}'>Open all in Apple Maps</a>"
        )
        if callback.message is not None and hasattr(callback.message, "edit_text"):
            await callback.message.edit_text(
                text=response,
                reply_markup=get_back_to_main_menu_keyboard(),
                parse_mode="HTML",
            )


@router.callback_query(F.data == "main_menu")
async def handle_main_menu(callback: CallbackQuery) -> None:
    """Handle the main menu request."""
    if callback.message is not None and isinstance(callback.message, Message):
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
        header = (
            f"{'Organization':<{name_width}} | {'USD':>7} | {'EUR':>7} | {'RUB':>7}"
        )
        sep = "─" * (name_width + 3 + 7 + 3 + 7 + 3 + 7)
        lines = [header, sep]
        for row in rows[:4]:  # NBG + 3 online banks
            org = row.organization
            usd = f"{row.usd:.4f}" if row.usd is not None else "-"
            eur = f"{row.eur:.4f}" if row.eur is not None else "-"
            rub = f"{row.rub:.4f}" if row.rub is not None else "-"
            lines.append(f"{org:<{name_width}} | {usd:>7} | {eur:>7} | {rub:>7}")
        table_str = "\n".join(lines)

        # Use current UTC time for latest_ts (no timestamp info in float values)
        latest_ts = datetime.now(UTC)
        # Convert to GMT+4
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
                currencies=options, callback_prefix="get_currency"
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
    if isinstance(callback.message, AiogramMessage) and callback.message.text:
        # Message text is like: 'Selected USD. What currency do you want to get?'
        import re

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
    # We'll need to fetch the actual Rate objects for each org/office
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
        if isinstance(callback.message, Message):  # type: ignore[attr-defined]
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
        if isinstance(callback.message, Message):  # type: ignore[attr-defined]
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

    if isinstance(callback.message, Message):  # type: ignore[attr-defined]
        await callback.message.edit_text(
            text=response,
            reply_markup=get_back_to_main_menu_keyboard(),
            parse_mode="HTML",
        )


@router.callback_query(F.data == "find_office_menu")
async def handle_find_office_menu(callback: CallbackQuery) -> None:
    """
    Show the office search options menu with explanation.
    """
    explanation = (
        "\u2139\ufe0f <b>Find Nearest Office</b>\n"
        "The first two options require you to share your location. "
        "If you do not want to share your location, you can still browse all offices by organization."
    )
    if callback.message is not None and isinstance(callback.message, Message):
        await callback.message.edit_text(
            text=explanation,
            reply_markup=get_find_office_menu_keyboard(),
            parse_mode="HTML",
        )


@router.callback_query(F.data == "find_nearest_office")
async def handle_find_nearest_office(callback: CallbackQuery) -> None:
    """
    Prompt the user to share their location for finding the nearest office.
    """
    user_id = callback.from_user.id if callback.from_user else None
    if user_id:
        user_search_state[user_id] = {"mode": "find_nearest_office"}
    text = (
        "Please share your location so we can find the nearest exchange office. "
        "Your location is only used for this search."
    )
    if callback.message is not None and isinstance(callback.message, Message):
        await callback.message.edit_text(
            text=text,
            reply_markup=get_location_or_fallback_keyboard(),
        )


@router.callback_query(F.data == "find_best_rate_office")
async def handle_find_best_rate_office(callback: CallbackQuery) -> None:
    """
    Ask the user to select a currency pair before prompting for location for best rate office search.
    """
    # Reuse currency selection logic (sell currency first)
    user_id = callback.from_user.id if callback.from_user else None
    if user_id:
        user_search_state[user_id] = {"mode": "find_best_rate_office"}
    if callback.message is not None and isinstance(callback.message, Message):
        await callback.message.edit_text(
            text="Which currency do you want to sell?",
            reply_markup=get_currency_selection_keyboard(
                currencies=AVAILABLE_BOT_CURRENCIES,
                callback_prefix="find_best_sell_currency",
            ),
        )


@router.callback_query(F.data.startswith("find_best_sell_currency:"))
async def handle_find_best_sell_currency(callback: CallbackQuery) -> None:
    """
    Handle sell currency selection for best rate office, then ask for get currency.
    """
    user_id = callback.from_user.id if callback.from_user else None
    sell_currency = callback.data.split(":")[1] if callback.data else ""
    options = [c for c in AVAILABLE_BOT_CURRENCIES if c != sell_currency]
    if user_id:
        state = user_search_state.setdefault(user_id, {"mode": "find_best_rate_office"})
        state["sell_currency"] = sell_currency
    if callback.message is not None and isinstance(callback.message, Message):
        await callback.message.edit_text(
            text=f"Selected {sell_currency}. What currency do you want to get?",
            reply_markup=get_currency_selection_keyboard(
                currencies=options,
                callback_prefix=f"find_best_get_currency:{sell_currency}",
            ),
        )


@router.callback_query(F.data.startswith("find_best_get_currency:"))
async def handle_find_best_get_currency(callback: CallbackQuery) -> None:
    """
    Handle get currency selection for best rate office, then prompt for location.
    """
    user_id = callback.from_user.id if callback.from_user else None
    parts = callback.data.split(":") if callback.data else []
    if len(parts) == 3:
        sell_currency = parts[1]
        get_currency = parts[2]
    else:
        sell_currency = "USD"
        get_currency = "GEL"
    if user_id:
        state = user_search_state.setdefault(user_id, {"mode": "find_best_rate_office"})
        state["sell_currency"] = sell_currency
        state["get_currency"] = get_currency
    text = (
        f"You selected {sell_currency} → {get_currency}.\n"
        "Please share your location so we can find the nearest office with the best rate for this pair."
    )
    if callback.message is not None and isinstance(callback.message, Message):
        await callback.message.edit_text(
            text=text,
            reply_markup=get_location_or_fallback_keyboard(),
        )


@router.callback_query(F.data == "find_office_by_org")
async def handle_find_office_by_org(callback: CallbackQuery) -> None:
    """
    Show a list of organizations filtered by type (Bank or MicrofinanceOrganization).
    """
    async with async_get_db_session() as session:
        org_repo = AsyncOrganizationRepository(session=session)
        orgs = await org_repo.get_active_organizations()
        orgs = [
            o
            for o in orgs
            if getattr(o, "type", None) in ("Bank", "MicrofinanceOrganization")
        ]
        organizations = [o.name for o in orgs]
    if callback.message is not None and isinstance(callback.message, Message):
        await callback.message.edit_text(
            text="Select an organization to view its offices:",
            reply_markup=get_organization_keyboard(organizations=organizations),
        )


@router.callback_query(F.data == "share_location")
async def handle_share_location(callback: CallbackQuery) -> None:
    """
    Prompt the user to share their location using a reply keyboard with request_location=True.
    """
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Share location", request_location=True)],
            [KeyboardButton(text="Cancel")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    if callback.message is not None:
        await callback.message.answer(
            "Please share your location using the button below.",
            reply_markup=keyboard,
        )
        await callback.answer()


@router.message(F.location)
async def handle_location_message(message: Message) -> None:
    """
    Handle user location message for office search.
    Determines context from user_search_state.
    """
    user_id = message.from_user.id if message.from_user else None
    if not user_id or not message.location:
        await message.reply("Could not determine user or location.")
        return
    state = user_search_state.get(user_id, {})
    lat = message.location.latitude
    lon = message.location.longitude
    async with async_get_db_session() as session:
        org_repo = AsyncOrganizationRepository(session=session)
        office_repo = AsyncOfficeRepository(session=session)
        rate_repo = AsyncRateRepository(session=session, model_class=Rate)
        # Filter orgs by type
        orgs = await org_repo.get_active_organizations()
        orgs = [
            o
            for o in orgs
            if getattr(o, "type", None) in ("Bank", "MicrofinanceOrganization")
        ]
        offices: list[Any] = []
        for org in orgs:
            org_offices = await office_repo.get_by_organization(org.id)
            for office in org_offices:
                office.organization = org  # Attach org to office for later use
            offices.extend(org_offices)
        if not offices:
            await message.reply("No offices found.")
            return

        # Find nearest office
        def office_distance(office):
            return haversine_distance(lat, lon, office.lat, office.lng)

        if state.get("mode") == "find_best_rate_office":
            sell = state.get("sell_currency", "USD")
            get = state.get("get_currency", "GEL")
            # Find best rate office (reuse CurrencyService logic)
            service = CurrencyService(org_repo, office_repo, rate_repo)
            best_offices = await service.get_best_rates_for_pair(
                sell_currency=sell, get_currency=get
            )
            # Map org name to office
            best_org_names = {r["organization"] for r in best_offices}
            offices = [o for o in offices if o.organization.name in best_org_names]
            if not offices:
                await message.reply("No offices with best rates found.")
                return
        nearest = min(offices, key=office_distance)
        distance_km = office_distance(nearest)
        # Fetch rates for this office
        office_rates = await rate_repo.get_rates_by_office(nearest.id, limit=10)
        rates_lines = []
        for rate in office_rates:
            rates_lines.append(f"{rate.currency}: {rate.buy:.4f} / {rate.sell:.4f}")
        rates_str = "\n".join(rates_lines) if rates_lines else "No rates available."
        # Map links
        gmaps = f"https://maps.google.com/?q={nearest.lat},{nearest.lng}"
        amap = f"http://maps.apple.com/?ll={nearest.lat},{nearest.lng}"
        text = (
            f"Nearest office: <b>{nearest.name}</b>\n"
            f"Organization: <b>{nearest.organization.name}</b> ({getattr(nearest.organization, 'type', '-')})\n"
            f"Address: {nearest.address}\n"
            f"Distance: {distance_km:.2f} km\n"
            f"<a href='{gmaps}'>Open in Google Maps</a> | <a href='{amap}'>Open in Apple Maps</a>\n\n"
            f"<b>Rates:</b>\n{rates_str}"
        )
        await message.answer(text, parse_mode="HTML")
    # Clear state after use
    user_search_state.pop(user_id, None)
    # Remove the reply keyboard and show main menu
    await message.answer(
        "Main menu:", reply_markup=get_main_menu_keyboard()
    )
