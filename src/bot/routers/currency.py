"""Router for currency exchange functionality."""

from aiogram import Router, F
from aiogram.types import CallbackQuery

from src.bot.keyboards.inline import (
    get_main_menu_keyboard,
    get_currency_selection_keyboard,
    get_organization_keyboard,
    get_back_to_main_menu_keyboard,
)

router = Router(name="currency_router")

# Available currencies - this should come from a service in the future
AVAILABLE_CURRENCIES = ["USD", "EUR", "GBP", "TRY", "RUB"]


@router.callback_query(F.data == "best_rates_to_gel")
async def handle_best_rates_to_gel(callback: CallbackQuery) -> None:
    """Handle the best rates to GEL request.

    Args:
        callback: The callback query.
    """
    # TODO: Implement actual rate fetching from CurrencyService
    rates = [
        "1 USD = 2.65 GEL (Bank of Georgia)",
        "1 EUR = 2.85 GEL (TBC Bank)",
        "1 GBP = 3.35 GEL (Liberty Bank)",
        "1 TRY = 0.085 GEL (ProCredit Bank)",
        "1 RUB = 0.029 GEL (Basis Bank)",
    ]

    response = "Top 5 best rates to GEL:\n\n" + "\n".join(rates)
    await callback.message.edit_text(
        text=response, reply_markup=get_back_to_main_menu_keyboard()
    )


@router.callback_query(F.data == "best_rates_between")
async def handle_best_rates_between(callback: CallbackQuery) -> None:
    """Handle the best rates between currencies request.

    Args:
        callback: The callback query.
    """
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
    from_currency = callback.data.split(":")[1]
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
    to_currency = callback.data.split(":")[1]  # noqa
    rates = [
        "1 USD = 0.93 EUR (Bank of Georgia)",
        "1 USD = 0.79 GBP (TBC Bank)",
        "1 USD = 31.18 TRY (Liberty Bank)",
        "1 USD = 91.38 RUB (ProCredit Bank)",
    ]

    response = "Top 5 best rates between currencies:\n\n" + "\n".join(rates)
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
    org_name = callback.data.split(":")[1]
    offices = [
        "Main Branch - Rustaveli Ave. 7",
        "Vake Branch - Chavchavadze Ave. 60",
        "Saburtalo Branch - Pekini Ave. 45",
        "Didube Branch - Agmashenebeli Ave. 120",
    ]

    response = f"Offices of {org_name}:\n\n" + "\n".join(offices)
    await callback.message.edit_text(
        text=response, reply_markup=get_back_to_main_menu_keyboard()
    )


@router.callback_query(F.data == "main_menu")
async def handle_main_menu(callback: CallbackQuery) -> None:
    """Handle the main menu request.

    Args:
        callback: The callback query.
    """
    await callback.message.edit_text(
        text="Welcome to the Currency Exchange Bot! Please select an option:",
        reply_markup=get_main_menu_keyboard(),
    )
