"""
Organization router for organization selection and office listing flows.

Handles organization selection menus and office listings with map links.
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from src.bot.keyboards.inline import (
    get_organization_keyboard,
    get_back_to_main_menu_keyboard,
)
from src.repositories.organization_repository import AsyncOrganizationRepository
from src.repositories.office_repository import AsyncOfficeRepository
from src.db.session import async_get_db_session
from src.bot.utils.map_links import (
    generate_google_maps_multi_pin_url,
    generate_apple_maps_multi_pin_url,
)

router = Router(name="org_router")


@router.callback_query(F.data == "find_office_by_org")
async def handle_find_office_by_org(callback: CallbackQuery) -> None:
    """Show a list of organizations filtered by type (Bank or MicrofinanceOrganization)."""
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


@router.callback_query(F.data.startswith("org:"))
async def handle_organization_selection(callback: CallbackQuery) -> None:
    """Handle the organization selection and show its offices with map links."""
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
        offices = await office_repo.get_by_organization(org.id)
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
