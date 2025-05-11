"""
Location router for office search and location-based flows.

Handles office search menus, location sharing, nearest office, and related filters.
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, ReplyKeyboardMarkup, KeyboardButton
from typing import Any
from src.bot.keyboards.inline import (
    get_find_office_menu_keyboard,
    get_currency_selection_keyboard,
    get_open_office_filter_keyboard,
    get_location_or_fallback_keyboard,
    get_back_to_main_menu_keyboard,
    get_main_menu_keyboard,
)
from src.services.currency_service import CurrencyService
from src.repositories.organization_repository import AsyncOrganizationRepository
from src.repositories.office_repository import AsyncOfficeRepository
from src.repositories.rate_repository import AsyncRateRepository
from src.config.logging_conf import get_logger
from src.db.session import async_get_db_session
from src.db.models.rate import Rate
from src.utils.schedule_parser import format_weekly_schedule
from src.bot.utils.logging_decorator import log_router_call

router = Router(name="location_router")
logger = get_logger(__name__)

AVAILABLE_BOT_CURRENCIES = ["USD", "EUR", "GBP", "RUB", "GEL"]

# Simple in-memory state for demo (user_id -> context)
user_search_state: dict[int, dict[str, Any]] = {}


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two points (km)."""
    from math import radians, cos, sin, sqrt, atan2

    R = 6371.0  # Earth radius in km
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = (
        sin(dlat / 2) ** 2
        + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    )
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c


@router.callback_query(F.data == "find_office_menu")
@log_router_call
async def handle_find_office_menu(callback: CallbackQuery) -> None:
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


@router.callback_query(F.data == "find_best_rate_office")
@log_router_call
async def handle_find_best_rate_office(callback: CallbackQuery) -> None:
    user_id = callback.from_user.id if callback.from_user else None
    if user_id:
        user_search_state[user_id] = {"mode": "find_best_rate_office"}
    text = "Would you like to see only currently open offices or all offices?"
    if callback.message is not None and isinstance(callback.message, Message):
        await callback.message.edit_text(
            text=text,
            reply_markup=get_open_office_filter_keyboard(),
        )


@router.callback_query(F.data.startswith("find_best_sell_currency:"))
@log_router_call
async def handle_find_best_sell_currency(callback: CallbackQuery) -> None:
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
@log_router_call
async def handle_find_best_get_currency(callback: CallbackQuery) -> None:
    parts = callback.data.split(":") if callback.data else []
    if len(parts) == 3:
        sell_currency = parts[1]
        get_currency = parts[2]
    else:
        sell_currency = "USD"
        get_currency = "GEL"
    text = (
        f"You selected {sell_currency} → {get_currency}.\n"
        "Would you like to see only currently open offices or all offices?"
    )
    if callback.message is not None and isinstance(callback.message, Message):
        await callback.message.edit_text(
            text=text,
            reply_markup=get_open_office_filter_keyboard(),
        )


@router.callback_query(F.data == "share_location")
@log_router_call
async def handle_share_location(callback: CallbackQuery) -> None:
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
@log_router_call
async def handle_location_message(message: Message) -> None:
    user_id = message.from_user.id if message.from_user else None
    if not user_id or not message.location:
        await message.reply("Could not determine user or location.")
        return
    state = user_search_state.get(user_id)
    if state is None:
        await message.reply(
            "Session expired or context lost. Returning to main menu.",
            reply_markup=get_main_menu_keyboard(),
        )
        return
    lat = message.location.latitude
    lon = message.location.longitude
    async with async_get_db_session() as session:
        org_repo = AsyncOrganizationRepository(session=session)
        office_repo = AsyncOfficeRepository(session=session)
        rate_repo = AsyncRateRepository(session=session, model_class=Rate)
        from src.repositories.schedule_repository import AsyncScheduleRepository
        from src.db.models.schedule import Schedule

        schedule_repo = AsyncScheduleRepository(session=session, model_class=Schedule)
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
                office.organization = org
            offices.extend(org_offices)
        offices = [o for o in offices if o.name.lower() not in ("express", "pawn")]
        if not offices:
            await message.reply("No offices found.")
            return
        open_status_map: dict[Any, bool] = {}
        if state.get("open_only") is True:
            from datetime import datetime
            import pytz

            now = datetime.now(pytz.timezone("Asia/Tbilisi"))
            weekday = now.weekday()
            now_minutes = now.hour * 60 + now.minute
            schedule_repo = AsyncScheduleRepository(
                session=session, model_class=Schedule
            )
            open_offices = []
            for office in offices:
                schedules = await schedule_repo.get_by_office_id(office.id)
                is_open = False
                for sched in schedules:
                    if (
                        sched.day == weekday
                        and sched.opens_at <= now_minutes < sched.closes_at
                    ):
                        is_open = True
                        break
                open_status_map[office.id] = is_open
                if is_open:
                    open_offices.append(office)
            offices = open_offices
            if not offices:
                await message.reply("No offices are currently open.")
                return
        else:
            from datetime import datetime
            import pytz

            now = datetime.now(pytz.timezone("Asia/Tbilisi"))
            weekday = now.weekday()
            now_minutes = now.hour * 60 + now.minute
            schedule_repo = AsyncScheduleRepository(
                session=session, model_class=Schedule
            )
            for office in offices:
                schedules = await schedule_repo.get_by_office_id(office.id)
                is_open = False
                for sched in schedules:
                    if (
                        sched.day == weekday
                        and sched.opens_at <= now_minutes < sched.closes_at
                    ):
                        is_open = True
                        break
                open_status_map[office.id] = is_open

        def office_distance(office):
            return haversine_distance(lat, lon, office.lat, office.lng)

        if state.get("mode") == "find_best_rate_office":
            sell = state.get("sell_currency", "USD")
            get = state.get("get_currency", "GEL")
            service = CurrencyService(org_repo, office_repo, rate_repo)
            best_offices = await service.get_best_rates_for_pair(
                sell_currency=sell, get_currency=get
            )
            best_org_names = {r["organization"] for r in best_offices}
            offices = [o for o in offices if o.organization.name in best_org_names]
            if not offices:
                await message.reply("No offices with best rates found.")
                return
        nearest = min(offices, key=office_distance)
        office_rates = await rate_repo.get_rates_by_office(nearest.id, limit=10)
        rates_lines = []
        for rate in office_rates:
            rates_lines.append(
                f"{rate.currency}: {rate.buy_rate:.4f} / {rate.sell_rate:.4f}"
            )
        rates_str = "\n".join(rates_lines) if rates_lines else "No rates available."
        open_status = open_status_map.get(nearest.id)
        open_status_str = (
            "<b>Status:</b> Open now" if open_status else "<b>Status:</b> Closed now"
        )
        office_schedules = await schedule_repo.get_by_office_id(nearest.id)
        schedule_dicts = [
            {"day": s.day, "opens_at": s.opens_at, "closes_at": s.closes_at}
            for s in office_schedules
        ]
        schedule_str = (
            format_weekly_schedule(schedule_dicts)
            if schedule_dicts
            else "No schedule info."
        )
        office_info = (
            f"🏢 <b>{nearest.name}</b>\n"
            f"{nearest.address}\n"
            f"{nearest.organization.name} ({getattr(nearest.organization, 'type', '-')})\n"
            f"{open_status_str}\n"
            f"\n🕒 <b>Working hours</b>:\n{schedule_str}"
            f"\n💱 <b>Rates</b>:\n{rates_str}"
        )
        await message.answer(
            office_info,
            parse_mode="HTML",
            reply_markup=get_back_to_main_menu_keyboard(),
        )
    user_search_state.pop(user_id, None)


@router.callback_query(F.data == "filter_open_only")
@log_router_call
async def handle_filter_open_only(callback: CallbackQuery) -> None:
    user_id = callback.from_user.id if callback.from_user else None
    if user_id:
        state = user_search_state.setdefault(user_id, {})
        state["open_only"] = True
    text = (
        "Please share your location so we can find the nearest currently open exchange office. "
        "Your location is only used for this search."
    )
    if callback.message is not None and isinstance(callback.message, Message):
        await callback.message.edit_text(
            text=text,
            reply_markup=get_location_or_fallback_keyboard(),
        )


@router.callback_query(F.data == "filter_all_offices")
@log_router_call
async def handle_filter_all_offices(callback: CallbackQuery) -> None:
    user_id = callback.from_user.id if callback.from_user else None
    if user_id:
        state = user_search_state.setdefault(user_id, {})
        state["open_only"] = False
    text = (
        "Please share your location so we can find the nearest exchange office. "
        "Your location is only used for this search."
    )
    if callback.message is not None and isinstance(callback.message, Message):
        await callback.message.edit_text(
            text=text,
            reply_markup=get_location_or_fallback_keyboard(),
        )


@router.callback_query(F.data == "find_nearest_office")
@log_router_call
async def handle_find_nearest_office(callback: CallbackQuery) -> None:
    user_id = callback.from_user.id if callback.from_user else None
    if user_id:
        user_search_state[user_id] = {"mode": "find_nearest_office"}
    text = "Would you like to see only currently open offices or all offices?"
    if callback.message is not None and isinstance(callback.message, Message):
        await callback.message.edit_text(
            text=text,
            reply_markup=get_open_office_filter_keyboard(),
        )
