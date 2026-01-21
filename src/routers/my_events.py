import datetime
from typing import Any

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from mako.pyparser import reserved

from database.orm import AsyncOrm
from database.schemas import User, EventUsersPayment, EventUsers, Payment
from src.keyboards import  get_inline_keyboard
from src import utils
from src import buttons as btn

from settings import settings
from logger import logger
from src.messages import event_card

router = Router()


@router.callback_query(F.data == "my_events")
async def my_events_list(callback: CallbackQuery, session: Any):
    """Мои события"""
    await callback.answer()
    wait_msg = await callback.message.edit_text(btn.WAIT)

    tg_id = str(callback.from_user.id)

    # Получаем пользователя
    user: User = await AsyncOrm.get_user_by_tg_id(tg_id, session)

    # Получаем основные и резервные события пользователя по платежам
    events: list[EventUsersPayment] = await AsyncOrm.get_events_payments_for_user(user.id, session)

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
        # Если ожидает оплаты
        else:
            status = "⏳"

        key = f"{status} {date} ({weekday}) {event.type}"
        value = f"my_events|{event.id}"
        buttons[key] = value
    keyboard = get_inline_keyboard(buttons, back_callback="main_menu")

    await wait_msg.edit_text(msg, reply_markup=keyboard.as_markup())


@router.callback_query(F.data.split("|")[0] == "my_events")
async def my_events_detail(callback: CallbackQuery, session: Any):
    """Карточка мероприятия в моих событиях"""
    await callback.answer()
    wait_msg = await callback.message.edit_text(btn.WAIT)

    event_id = int(callback.data.split("|")[1])
    tg_id = str(callback.from_user.id)

    # Получаем пользователя
    user: User = await AsyncOrm.get_user_by_tg_id(tg_id, session)

    # Получаем событие с участниками и резервом
    event: EventUsers = await AsyncOrm.get_event_with_users(event_id, session)
    is_reserve_event = user.id in [u.id for u in event.reserved]

    # Получаем платеж пользователя на это событие
    payment: Payment | None = await AsyncOrm.get_payment(tg_id, event_id, session)

    # Карточка события
    msg = event_card(event, payment)

    # Сборка клавиатуры
    buttons = {}

    # Если пользователю подтверждена оплата
    if payment.paid_confirm:
        # Если пользователь в резерве
        if is_reserve_event:
            buttons["❌ Отменить запись в резерв"] = f"unreg_user_reserve|{event.id}"
        # Если пользователь в основе
        else:
            buttons["❌ Отменить запись"] = f"unreg_user|{event.id}"

    kb = get_inline_keyboard(buttons=buttons, back_callback=f"my_events")

    await wait_msg.edit_text(msg, reply_markup=kb.as_markup(), disable_web_page_preview=True)
