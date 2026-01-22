import datetime

from aiogram.filters import Command
from typing import Any

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from database.orm import AsyncOrm
from database.schemas import AddEvent, Event, EventUsers
from logger import logger
from settings import settings
from src.messages import event_card
from src.states import AddEventFSM
from src.keyboards import cancel_keyboard, get_inline_keyboard, admin_event_keyboard
from src import utils
from src.middlewares import AdminMiddleware
from src import buttons as btn
from src.utils import convert_date_named_month, convert_time

router = Router()
router.message.middleware.register(AdminMiddleware())
router.callback_query.middleware.register(AdminMiddleware())


@router.message(Command("events"))
@router.callback_query(F.data == "admin-events")
async def admin_active_events(message: Message | CallbackQuery, session: Any):
    """События для админа"""
    events: list[Event] = await AsyncOrm.get_events(session, only_active=True)

    msg = "События" if events else "Событий пока нет"

    buttons = {}
    for event in events:
        date = utils.convert_date_named_month(event.date)
        time = utils.convert_time(event.date)
        key = f"{date} {time} {event.type}"
        buttons[key] = f"admin-event|{event.id}"

    keyboard = get_inline_keyboard(buttons)

    if isinstance(message, Message):
        await message.answer(msg, reply_markup=keyboard.as_markup())
    else:
        await message.answer()
        await message.message.answer(msg, reply_markup=keyboard.as_markup())


@router.callback_query(F.data.split("|")[0] == "admin-event")
async def admin_event_card(callback: CallbackQuery, session: Any):
    """Карточка события для администратора"""
    await callback.answer()

    event_id = int(callback.data.split("|")[1])

    event: EventUsers = await AsyncOrm.get_event_with_users(event_id, session)

    msg = event_card(event, payment=None, for_admin=True)
    msg += "\nЧтобы удалить участника с события, нажмите кнопку с соответствующим номером участника"

    keyboard = admin_event_keyboard(event)

    await callback.message.edit_text(msg, reply_markup=keyboard.as_markup(), disable_web_page_preview=True)


@router.callback_query(F.data.split("|")[0] == "admin-event-user")
async def delete_user_from_event(callback: CallbackQuery):
    """Запрос удаления участника события"""
    await callback.answer()

    event_id = int(callback.data.split("|")[1])
    user_id = int(callback.data.split("|")[2])

    msg = "Удалить пользователя с события?"
    keyboard = get_inline_keyboard(
        {
            "Да": f"admin-event-delete-user|{event_id}|{user_id}",
            "Нет": f"admin-event|{event_id}"
        }
    )
    await callback.message.edit_text(msg, reply_markup=keyboard.as_markup())


@router.callback_query(F.data.split("|")[0] == "admin-event-delete-user")
async def delete_user_from_event_confirmed(callback: CallbackQuery, session: Any):
    """Удаление участника события"""
    await callback.answer()

    admin_tg_id = str(callback.from_user.id)
    event_id = int(callback.data.split("|")[1])
    user_id = int(callback.data.split("|")[2])

    event: EventUsers = await AsyncOrm.get_event_with_users(event_id, session)

    try:
        # Удаление пользователя с события
        await AsyncOrm.delete_user_from_event(event_id, user_id, session)

        # Удаление платежа пользователя
        await AsyncOrm.delete_payment(event_id, user_id, session)

        # Оповещение администратора
        await callback.message.edit_text("Пользователь удален с события ✅")
        logger.info(f"Администратор {admin_tg_id} удалил пользователя id {user_id} с события id {event_id}")

    except:
        await callback.message.edit_text(f"{btn.INFO} Ошибка при удалении участника. Повторите запрос позже")
        return

    # Добор из резерва
    if event.reserved:
        user_for_transfer = event.reserved[0]

        # Переносим человека из резерва
        try:
            await AsyncOrm.transfer_user_from_reserve(event_id, user_for_transfer.id, session)

            # Оповещение человека записанного из резерва
            date = convert_date_named_month(event.date)
            time = convert_time(event.date)
            user_msg = f"🔔 <b>Автоматическое уведомление</b>\n\n" \
                       f"Вы записаны на <b>{event.type}</b> {event.title} на " \
                       f"<b>{date}</b> в <b>{time}</b> " \
                       f"из резерва, так как один из участников отменил запись"
            await callback.bot.send_message(user_for_transfer.tg_id, user_msg)
        except:
            await callback.message.answer(f"{btn.INFO} Ошибка при доборе пользователя из резерва.")
            return

    # Возврат к карточке мероприятия
    event: EventUsers = await AsyncOrm.get_event_with_users(event_id, session)
    msg = event_card(event, payment=None, for_admin=True) + "\nЧтобы удалить участника с события, нажмите кнопку с соответствующим номером участника"
    keyboard = admin_event_keyboard(event)
    await callback.message.answer(msg, reply_markup=keyboard.as_markup(), disable_web_page_preview=True)


# DELETE EVENT
@router.callback_query(F.data.split("|")[0] == "admin-event-delete")
async def delete_event(callback: CallbackQuery, session: Any):
    """Удаление события"""
    await callback.answer()

    # Получаем событие
    event_id = int(callback.data.split("|")[1])
    event: EventUsers = await AsyncOrm.get_event_with_users(event_id, session)

    # Сообщение
    date = utils.convert_date(event.date)
    time = utils.convert_time(event.date)
    msg = f"Вы действительно хотите удалить событие <b>{event.type} \"{event.title}\"</b> {date} в {time}?"

    # Клавиатура
    buttons = {
        "Да": f"admin-delete-event-confirm|{event_id}",
        "Нет": f"admin-event|{event_id}"
    }
    keyboard = get_inline_keyboard(buttons)

    await callback.message.edit_text(msg, reply_markup=keyboard.as_markup())


@router.callback_query(F.data.split("|")[0] == "admin-delete-event-confirm")
async def delete_event_confirm(callback: CallbackQuery, session: Any):
    """Подтверждение удаления события"""
    await callback.answer()

    # Получаем событие
    event_id = int(callback.data.split("|")[1])
    event: EventUsers = await AsyncOrm.get_event_with_users(event_id, session)

    # Удаляем событие
    try:
        await AsyncOrm.delete_event(event_id, session)

        # Оповещаем админа
        await callback.message.edit_text("Событие удалено ✅")

        # Возврат админа к списку событий
        events: list[Event] = await AsyncOrm.get_events(session, only_active=True)
        msg = "События" if events else "Событий пока нет"
        buttons = {}
        for e in events:
            date = utils.convert_date_named_month(e.date)
            time = utils.convert_time(e.date)
            key = f"{date} {time} {e.type}"
            buttons[key] = f"admin-event|{e.id}"
        keyboard = get_inline_keyboard(buttons)
        await callback.message.answer(msg, reply_markup=keyboard.as_markup())

        admin_tg_id = str(callback.from_user.id)
        date = utils.convert_date(event.date)
        time = utils.convert_time(event.date)
        logger.info(f"Администратор {admin_tg_id} удалил событие {event.type} {event.title} {date} {time}")

        # Оповещаем пользователей
        user_message = f"🔔 <b>Автоматическое уведомление</b>\n\n" \
                  f"Событие <b>\"{event.title}\"</b>, запланированное <b>{date}</b> в <b>{time}</b>, " \
                  f"<b>отменено администратором</b>\n\n" \
                  f"По вопросу возврата оплаты обращайтесь к администратору @{settings.admin_tg_username}"

        # Оповещаем пользователей основы
        for user in event.users:
            try:
                await callback.bot.send_message(user.tg_id, user_message)
            except Exception as e:
                logger.error(f"Ошибка оповещения основного пользователя id {user.id} об отмене события id {event_id}: {e}")

        # Оповещаем пользователей резерва
        for user in event.reserved:
            try:
                await callback.bot.send_message(user.tg_id, user_message)
            except Exception as e:
                logger.error(f"Ошибка оповещения резервного пользователя id {user.id} об отмене события id {event_id}: {e}")

    except Exception:
        await callback.message.edit_text(f"{btn.INFO} Ошибка при удалении события. Повторите запрос позже")
        return








