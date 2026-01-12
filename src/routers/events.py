from typing import Any

from aiogram import Router, F
from aiogram.types import CallbackQuery

from database.orm import AsyncOrm
from src.keyboards import date_keyboard
from src import utils

router = Router()

@router.callback_query(F.data == "all_events")
async def show_all_events(callback: CallbackQuery, session: Any):
    """Вывод всех событий по датам"""
    await callback.answer()

    # Получаем события на ближайшие N дней
    events = await AsyncOrm.get_upcoming_events(session)

    # Получаем дни в которых есть мероприятие
    active_dates = utils.get_active_dates(events)

    msg = "Даты с событиями:"
    if not events:
        msg = "В ближайшее время нет событий"

    keyboard = date_keyboard(active_dates)

    await callback.message.edit_text(msg, reply_markup=keyboard.as_markup())

