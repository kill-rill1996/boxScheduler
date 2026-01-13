from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src import buttons as btn
from src.utils import get_weekday_from_date


def cancel_keyboard() -> InlineKeyboardBuilder:
    """Клавиатура для отмены"""
    keyboard = InlineKeyboardBuilder()

    keyboard.row(
        InlineKeyboardButton(text=btn.CANCEL, callback_data="cancel")
    )

    return keyboard

def get_inline_keyboard(
        buttons: dict,
        in_row: int = None,
        back_callback: str = None,
        cancel_button: bool = False,
    ) -> InlineKeyboardBuilder:
    """Создание inline keyboard"""
    keyboard = InlineKeyboardBuilder()

    for text, callback in buttons.items():
        keyboard.row(
            InlineKeyboardButton(text=text, callback_data=callback)
        )

    if in_row:
        keyboard.adjust(in_row)

    if back_callback:
        keyboard.row(
            InlineKeyboardButton(text=btn.BACK, callback_data=back_callback)
        )

    if cancel_button:
        keyboard.row(
            InlineKeyboardButton(text=btn.CANCEL, callback_data="cancel")
        )

    return keyboard

def main_menu_keyboard() -> InlineKeyboardBuilder:
    """Клавиатура главного меню"""
    keyboard = get_inline_keyboard(
        {
            btn.ALL_EVENTS: "all_events",
            btn.PROFILE: "profile",
            btn.MY_EVENTS: "my_events",
        },
        in_row=2,
    )
    return keyboard


def date_keyboard(active_date: dict[str, int]) -> InlineKeyboardBuilder:
    """Клавиатура с датами и кол-вом мероприятий"""
    keyboard = InlineKeyboardBuilder()

    for key in active_date.keys():
        weekday = get_weekday_from_date(key)
        count = active_date[key]

        if count == 1:
            events = "мероприятие"
        elif count in [2, 3, 4]:
            events = "мероприятия"
        else:
            events = "мероприятий"

        callback_data = f"events-date|{key}"

        keyboard.row(
            InlineKeyboardButton(text=f"{key} {weekday} ({count} {events})", callback_data=callback_data)
        )

    keyboard.row(
        InlineKeyboardButton(text=btn.BACK, callback_data="main_menu")
    )

    keyboard.adjust(1)
    return keyboard