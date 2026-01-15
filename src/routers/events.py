from calendar import weekday
from typing import Any
from datetime import datetime

import pytz
from aiogram import Router, F
from aiogram.filters import or_f
from aiogram.types import CallbackQuery
from aiogram.utils import keyboard

from database.orm import AsyncOrm
from database.schemas import Event, EventUsers, User, Payment, AddPayment
from src.keyboards import date_keyboard, get_inline_keyboard, main_menu_keyboard
from src import utils
from src import buttons as btn
from src.messages import event_card, invoice_message_for_user, main_menu_message
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
            f"all_events|{event.id}|{date_str}" for event in events
    }
    keyboard = get_inline_keyboard(buttons, in_row=1, back_callback="all_events")

    await callback.message.edit_text(msg, reply_markup=keyboard.as_markup())


@router.callback_query(F.data.split("|")[0] == "all_events")
async def event_details(callback: CallbackQuery, session: Any):
    """Вывод информации по событию"""
    await callback.answer()

    event_id = int(callback.data.split("|")[1])
    # Для кнопки назад
    date_str = callback.data.split("|")[2]
    tg_id = str(callback.from_user.id)

    # Получаем событие с участниками и резервом
    event: EventUsers = await AsyncOrm.get_event_with_users(event_id, session)
    event_is_full: bool = len(event.users) >= event.places

    # Получаем платеж пользователя на это событие
    payment: Payment | None = await AsyncOrm.get_payment(tg_id, event_id, session)

    msg = event_card(event, payment)

    # Сборка клавиатуры
    buttons = {}

    # Если пользователь еще не записался
    if not payment:
        # Если событие уже заполнено
        if event_is_full:
            buttons["📝 Записаться в резерв"] = f"reg-user-reserve|{event_id}|{date_str}"
        # Если есть свободные места
        else:
            buttons["✅ Записаться"] = f"reg-user|{event_id}|{date_str}"

    kb = get_inline_keyboard(
        buttons=buttons,
        back_callback=f"events-date|{date_str}"
    )

    await callback.message.edit_text(msg, reply_markup=kb.as_markup(), disable_web_page_preview=True)


@router.callback_query(or_f(F.data.split("|")[0] == "reg-user", F.data.split("|")[0] == "reg-user-reserve"))
async def registration_user_in_event(callback: CallbackQuery, session: Any):
    """Запись на мероприятия в основу и резерв"""
    await callback.answer()

    event_id = int(callback.data.split("|")[1])
    date_str = callback.data.split("|")[2]

    # Определение запись в основу или резерв
    to_reserve = callback.data.split("|")[0] == "reg-user-reserve"

    # Проверка на свободные места
    event: EventUsers = await AsyncOrm.get_event_with_users(event_id, session)
    event_is_full: bool = len(event.users) >= event.places

    # Для записи в основу (на случай нажатия одновременно,
    # либо очень позднее нажатие на старое сообщение, которое с кнопкой записи)
    if event_is_full and not to_reserve:
        await callback.message.edit_text("❗Вы не можете записаться на данное событие, "
                                         "так как свободных мест нет")
        return

    # Отправка сообщения
    msg = invoice_message_for_user(event, to_reserve=to_reserve)

    if to_reserve:
        buttons = {"Оплатил(а)": f"paid-reserve|{event.id}"}
    else:
        buttons = {"Оплатил(а)": f"paid|{event.id}"}

    keyboard = get_inline_keyboard(buttons, back_callback=f"all_events|{event_id}|{date_str}")
    await callback.message.edit_text(msg, disable_web_page_preview=True,reply_markup=keyboard.as_markup())


@router.callback_query(or_f(F.data.split("|")[0] == "paid", F.data.split("|")[0] == "paid-reserve"))
async def confirmation_payment_by_user(callback: CallbackQuery, session: Any):
    """Подтверждение оплаты пользователем"""
    await callback.answer()

    event_id = int(callback.data.split("|")[1])
    tg_id = str(callback.from_user.id)

    # Определение запись в резерв или основу
    to_reserve: bool = callback.data.split("|")[0] == "paid-reserve"

    # Получаем событие
    event: EventUsers = await AsyncOrm.get_event_with_users(event_id, session)
    event_is_full: bool = len(event.users) >= event.places

    # Если мероприяитие уже неактивно
    if not event.active:
        await callback.message.edit_text(
            "⚠️ Запись невозможна, так как данное событие уже недоступно\n\nВы можете посмотреть доступные"
            " события в главном меню /menu во вкладке \"🗓️ Все события\"", )
        return

    # Проверка на свободные места
    # (если места кончились в процессе записи)
    if event_is_full and not to_reserve:
        await callback.message.edit_text("❗Не удалось записаться на событие, так как все места уже заняты.\n\n"
                                         f"Для возврата оплаты, свяжитесь с администратором @{settings.admin_tg_username}")

        # Оповещение администратора о необходимости вернуть деньги
        user: User = await AsyncOrm.get_user_by_tg_id(tg_id, session)
        date = utils.convert_date_named_month(event.date)
        time = utils.convert_time(event.date)
        msg_to_admin = f"❗❗Пользователь <a href='tg://user?id={user.tg_id}'>{user.firstname} {user.lastname}</a> перевел оплату за событие " \
                       f"<b>{event.type}</b> \"{event.title}\" <b>{date} {time}</b> <b>{event.price} руб.</b>, " \
                       f"но не был записан, так как во время записи свободные места кончились.\n\n" \
                       f"Необходимо вернуть пользователю оплату в размере <b>{event.price} руб.</b>"
        await callback.bot.send_message(settings.admin_tg_id, msg_to_admin)
        return

    # Создание платежа
    try:
        user: User = await AsyncOrm.get_user_by_tg_id(tg_id, session)
        payment = AddPayment(
            event_id=event_id,
            user_id=user.id,
            paid=True,
            paid_confirm=False
        )
        await AsyncOrm.create_payment(payment, session)
    except:
        await callback.message.edit_text("Произошла ошибка, попробуйте позже или обратитесь к администратору "
                                         f"@{settings.admin_tg_username}")
        return

    # Ответ пользователю
    user_msg = f"🔔 <b>Автоматическое уведомление</b>\n\n"\
               f"Ваш платеж на сумму {event.price} руб. ожидает подтверждение администратором @{settings.admin_tg_username}. "\
               f"После подтверждения вам будет отправлено уведомление о записи {'<b>в резерв события</b>' if to_reserve else 'на событие'}.\n\n"\
               f"⏳ <b>Дождитесь подтверждения оплаты от администратора</b>\n\n" \
               f"Вы можете отслеживать статус оплаты во вкладке \"{btn.MAIN_MENU}\" в разделе \"{btn.MY_EVENTS}\""

    await callback.message.edit_text(user_msg)
    # Перевод в главное меню
    msg = main_menu_message()
    keyboard = main_menu_keyboard()
    await callback.message.answer(msg, reply_markup=keyboard.as_markup())

    # Уведомление администратора
    date = utils.convert_date_named_month(event.date)
    time = utils.convert_time(event.date)
    admin_msg = f"Пользователь <a href='tg://user?id={user.tg_id}'>{user.firstname} {user.lastname}</a> " \
                f"оплатил {'<b>запись в резерв</b> события ' if to_reserve else ''}<b>{event.type}</b> \"{event.title}\" <b>{date} {time}</b> " \
                f"на сумму <b>{event.price} руб.</b> \n\nПодтвердите или отклоните оплату"
    if to_reserve:
        buttons = {
            "Подтвердить ✅": f"admin-payment-reserve|ok|{event_id}|{user.id}",
            "Отклонить ❌": f"admin-payment-reserve|cancel|{event_id}|{user.id}"
        }
    else:
        buttons = {
            "Подтвердить ✅": f"admin-payment|ok|{event_id}|{user.id}",
            "Отклонить ❌": f"admin-payment|cancel|{event_id}|{user.id}"
        }
    keyboard = get_inline_keyboard(buttons)
    await callback.bot.send_message(settings.admin_tg_id, admin_msg, reply_markup=keyboard.as_markup())
