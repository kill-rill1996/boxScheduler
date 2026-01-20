import datetime
from typing import Any

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from database.orm import AsyncOrm
from database.schemas import User, EventUsersPayment
from src.keyboards import  get_inline_keyboard
from src import utils
from src import buttons as btn

from settings import settings
from logger import logger

router = Router()


@router.callback_query(F.data == "my_events")
async def my_events_list(callback: CallbackQuery, session: Any):
    """Мои события"""
    await callback.answer()
    wait_msg = await callback.message.edit_text(btn.WAIT)

    tg_id = str(callback.from_user.id)

    # Получаем пользователя
    user: User = await AsyncOrm.get_user_by_tg_id(tg_id, session)

    # Получаем основные и резервные события пользователя TODO rework
    events: list[EventUsersPayment] = await AsyncOrm.get_events_for_user(user.id, session)

    # Текст сообщения
    if not events:
        msg = "Вы пока никуда не записаны\n\nВы можете это сделать во вкладке \n\"🗓️ Все события\""
    else:
        msg = "<b>События куда вы записались:</b>\n\n" \
              "✅ - оплаченные события\n" \
              "📝 - резерв на событие\n" \
              "⏳ - ожидается подтверждение оплаты от администратора"

    # Подготовка клавиатуры
    buttons = {}

    for event in events:
        date = utils.convert_date(event.date)
        weekday = settings.weekdays[datetime.datetime.weekday(event.date)]

        # Если пользователь в резерве
        if user.id in [user.id for user in event.reserved]:
            status = "📝"
        # Если пользователь в основе
        elif event.payment.paid_confirm:
            status = "✅️"
        # Если ожидает оплаты TODO не работает
        else:
            status = "⏳"

        key = f"{status} {date} ({weekday}) {event.type}"
        value = f"my_events|{event.id}"
        buttons[key] = value
    keyboard = get_inline_keyboard(buttons, back_callback="main_menu")

    for e in events:
        logger.info(e.payment.paid_confirm)

    await wait_msg.edit_text(msg, reply_markup=keyboard.as_markup())