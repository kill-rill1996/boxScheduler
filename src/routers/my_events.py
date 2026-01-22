import datetime
from typing import Any

from aiogram import Router, F
from aiogram.filters import or_f
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


@router.callback_query(or_f(F.data.split("|")[0] == "unreg_user_reserve", F.data.split("|")[0] == "unreg_user"))
async def unreg_user(callback: CallbackQuery, session: Any):
    """Отмена записи в основу и резерв"""
    await callback.answer()

    event_id = int(callback.data.split("|")[1])
    is_reserve: bool = callback.data.split("|")[0] == "unreg_user_reserve"

    # Получаем событие
    event: EventUsers = await AsyncOrm.get_event_with_users(event_id, session)
    date = utils.convert_date(event.date)
    time = utils.convert_time(event.date)

    # Сообщение
    if is_reserve:
        msg = f"<b>Вы действительно хотите отменить свою запись в резерв на событие \"{event.type}\" {date} в {time}?</b>"
    else:
        msg = f"<b>Вы действительно хотите отменить свою запись на событие \"{event.type}\" {date} в {time}?</b>"

    # Клавиатура
    buttons = {}
    if is_reserve:
        value = f"unreg_reserve_confirmed|{event_id}"
    else:
        value = f"unreg_confirmed|{event_id}"
    buttons["Да"] = value
    buttons["Нет"] = f"my_events|{event_id}"
    keyboard = get_inline_keyboard(buttons)

    await callback.message.edit_text(msg, reply_markup=keyboard.as_markup())


@router.callback_query(or_f(F.data.split("|")[0] == "unreg_reserve_confirmed", F.data.split("|")[0] == "unreg_confirmed"))
async def unreg_user_confirmed(callback: CallbackQuery, session: Any):
    """Отмена записи подтверждена"""
    await callback.answer()

    event_id = int(callback.data.split("|")[1])
    tg_id = str(callback.from_user.id)
    is_reserve: bool = callback.data.split("|")[0] == "unreg_reserve_confirmed"

    # Получаем событие и пользователя
    event: EventUsers = await AsyncOrm.get_event_with_users(event_id, session)
    user: User = await AsyncOrm.get_user_by_tg_id(tg_id, session)

    # Отменяем запись
    try:
        if is_reserve:
            await AsyncOrm.unreg_user_reserve(event_id, user.id, session)
            logger.info(f"Пользователь id {user.id} отменил запись в резерв на событие id {event_id}")
        else:
            await AsyncOrm.delete_user_from_event(event_id, user.id, session)
            logger.info(f"Пользователь id {user.id} отменил запись на событие id {event_id}")

        # Удаление платежа
        await AsyncOrm.delete_payment(event_id, user.id, session)
    except:
        await callback.message.edit_text(f"{btn.INFO} Произошла ошибка, попробуйте позже")
        return

    # Ответ пользователю
    date = utils.convert_date(event.date)
    time = utils.convert_time(event.date)
    user_msg = f"🔔 <b>Автоматическое уведомление</b>\n\n" \
               f"<b>Вы отменили запись {'в резерв ' if is_reserve else ''}на событие \"{event.type}\" {date} " \
               f"в {time}</b>\n\nДля возврата оплаты, свяжитесь с администратором @{settings.admin_tg_username}"
    await callback.message.edit_text(user_msg)

    # Возврат к моим мероприятиям
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
    await callback.message.answer(msg, reply_markup=keyboard.as_markup())

    # Добираем из резерва (если отмена записи не из основы и есть люди в резерве)
    if not is_reserve and event.reserved:
        # Переводим из резерва в основу
        transfered_user = event.reserved[0]
        try:
            await AsyncOrm.transfer_user_from_reserve(event_id, transfered_user.id, session)
            transfer_is_successful = True
        except Exception as e:
            logger.error(f"Ошибка при перемещении пользователя id {transfered_user.id} из резерва "
                         f"в основу события id {event_id} после отмены записи пользователем id {user.id}: {e}")
            transfer_is_successful = False

        # Оповещение человека записанного из резерва (только при удачной попытке перемещения)
        if transfer_is_successful:
            try:
                notify_msg = f"🔔 <b>Автоматическое уведомление</b>\n\n" \
                             f"Вы записаны на <b>{event.type}</b> {event.title} на " \
                             f"<b>{date}</b> в <b>{time}</b> " \
                             f"из резерва, так как один из участников отменил запись"

                await callback.bot.send_message(transfered_user.tg_id, notify_msg)
            except Exception as e:
                logger.error(f"Ошибка при оповещении пользователя id {transfered_user.id} о перемещении из резерва в основу "
                             f"события id {event_id}: {e}")

    # Оповещение админа при отмене записи из основы
    if not is_reserve:
        admin_message = f"🔔 <b>Автоматическое уведомление</b>\n\n" \
                        f"Пользователь <b>{user.username} {user.lastname}</b> отменил запись на <b>{event.type}</b> {event.title} на " \
                        f"<b>{date}</b> в <b>{time}</b>"
        try:
            await callback.bot.send_message(settings.admin_tg_id, admin_message)
        except:
            pass
