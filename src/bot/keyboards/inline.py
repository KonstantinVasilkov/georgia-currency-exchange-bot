"""Inline keyboard layouts for the bot."""

from typing import Sequence

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Get the main menu keyboard.

    Returns:
        InlineKeyboardMarkup: The main menu keyboard.
    """
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="Best rates to GEL", callback_data="best_rates_to_gel"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Best rates between currencies", callback_data="best_rates_between"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Available organizations", callback_data="list_organizations"
        )
    )
    return builder.as_markup()


def get_currency_selection_keyboard(
    currencies: Sequence[str], callback_prefix: str
) -> InlineKeyboardMarkup:
    """Get the currency selection keyboard.

    Args:
        currencies: List of available currencies.
        callback_prefix: Prefix for callback data.

    Returns:
        InlineKeyboardMarkup: The currency selection keyboard.
    """
    builder = InlineKeyboardBuilder()
    for currency in currencies:
        builder.row(
            InlineKeyboardButton(
                text=currency, callback_data=f"{callback_prefix}:{currency}"
            )
        )
    builder.row(
        InlineKeyboardButton(text="Back to main menu", callback_data="main_menu")
    )
    return builder.as_markup()


def get_organization_keyboard(organizations: Sequence[str]) -> InlineKeyboardMarkup:
    """Get the organization selection keyboard.

    Args:
        organizations: List of available organizations.

    Returns:
        InlineKeyboardMarkup: The organization selection keyboard.
    """
    builder = InlineKeyboardBuilder()
    for org in organizations:
        builder.row(InlineKeyboardButton(text=org, callback_data=f"org:{org}"))
    builder.row(
        InlineKeyboardButton(text="Back to main menu", callback_data="main_menu")
    )
    return builder.as_markup()


def get_back_to_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Get the back to main menu keyboard.

    Returns:
        InlineKeyboardMarkup: The back to main menu keyboard.
    """
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Back to main menu", callback_data="main_menu")
    )
    return builder.as_markup()
