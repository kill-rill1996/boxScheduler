from calendar import weekday
from typing import Any
from datetime import datetime

import pytz
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils import keyboard

from database.orm import AsyncOrm
from database.schemas import Event
from src.keyboards import date_keyboard, get_inline_keyboard
from src import utils
from src.messages import event_card
from src.utils import convert_date_named_month

from settings import settings

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


@router.callback_query(F.data.split("|")[0] == "events-date")
async def show_event_in_date(callback: CallbackQuery, session: Any):
    """Вывод событий в определенную дату"""
    await callback.answer()

    # Получаем дату в str формате
    date_str = callback.data.split("|")[1]
    # Переводим в объект date
    date = datetime.strptime(date_str, "%d.%m.%Y")

    # Получаем события в этот день
    events: list[Event] = await AsyncOrm.get_events_by_date(date, session)

    # Переводим дату в формат для вывода в сообщение
    converted_date = convert_date_named_month(date)

    # Получаем день недели и формируем сообщение
    weekday = settings.weekdays[date.weekday()]
    msg = f"События на <b>{converted_date} ({weekday})</b>:\n\n" \
          f"События, на которые вы уже записаны, помечены '✅️'\n" \
          f"События, на которые вы записаны в резерв, помечены '📝'"

    # Создаем клавиатуру TODO доделать с записанными и резервом
    buttons = {
        f"{event.date.astimezone(pytz.timezone('Europe/Moscow')).time().strftime('%H:%M')} {event.type}":
            f"all_events|{event.id}" for event in events
    }
    keyboard = get_inline_keyboard(buttons, in_row=1, back_callback="all_events")

    await callback.message.edit_text(msg, reply_markup=keyboard.as_markup())


@router.callback_query(F.data.split("|")[0] == "all_events")
async def event_details(callback: CallbackQuery, session: Any):
    """Вывод информации по событию"""
    await callback.answer()

    event_id = int(callback.data.split("|")[1])

    # Получаем событие
    event: Event = await AsyncOrm.get_event_by_id(event_id, session)

    msg = event_card(event)

    await callback.message.answer(msg, disable_web_page_preview=True,)

    # TODO users registered, payment

