from aiogram.types import InlineKeyboardMarkup
from src.bot.keyboards.inline import (
    get_main_menu_keyboard,
    get_find_office_menu_keyboard,
)


def test_main_menu_keyboard_contains_find_office() -> None:
    keyboard: InlineKeyboardMarkup = get_main_menu_keyboard()
    buttons = [btn for row in keyboard.inline_keyboard for btn in row]
    texts = [btn.text for btn in buttons]
    assert "Find Nearest Office" in texts
    assert any(btn.callback_data == "find_office_menu" for btn in buttons)


def test_find_office_menu_keyboard_options() -> None:
    keyboard: InlineKeyboardMarkup = get_find_office_menu_keyboard()
    buttons = [btn for row in keyboard.inline_keyboard for btn in row]
    texts = [btn.text for btn in buttons]
    callback_data = [btn.callback_data for btn in buttons]
    assert "Find nearest office (share location)" in texts
    assert "Find nearest office with best rates (share location)" in texts
    assert "Show all offices of a chosen organization" in texts
    assert "Back to main menu" in texts
    assert "find_nearest_office" in callback_data
    assert "find_best_rate_office" in callback_data
    assert "find_office_by_org" in callback_data
    assert "main_menu" in callback_data
