import datetime

from aiogram.filters import Command
from typing import Any

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from database.orm import AsyncOrm
from database.schemas import AddEvent
from logger import logger
from src.states import AddEventFSM
from src.keyboards import cancel_keyboard
from src import utils
from src.middlewares import AdminMiddleware


router = Router()
router.message.middleware.register(AdminMiddleware())
router.callback_query.middleware.register(AdminMiddleware())

@router.message(Command("add_event"))
async def add_event_start(message: Message, state: FSMContext):
    """Начало создания события"""
    msg = await message.answer("Отправьте тип события (например тренировка)",
                               reply_markup=cancel_keyboard().as_markup())
    await state.set_state(AddEventFSM.type)
    await state.update_data(prev_mess=msg)


@router.message(AddEventFSM.type)
async def get_type(message: Message, state: FSMContext):
    """Получение типа, запрос названия"""
    # Меняем предыдущее сообщение
    data = await state.get_data()
    try:
        await data["prev_mess"].edit_text(data["prev_mess"].html_text)
    except:
        pass

    # Сохраняем данные
    type = message.text
    await state.update_data(type=type)

    # Меняем стейт
    await state.set_state(AddEventFSM.title)

    # Запрос названия
    msg = await message.answer("Отправьте описание события, не указывая дату",
                               reply_markup=cancel_keyboard().as_markup())
    await state.update_data(prev_mess=msg)


@router.message(AddEventFSM.title)
async def get_title(message: Message, state: FSMContext):
    """Получение названия, запрос даты"""
    # Меняем предыдущее сообщение
    data = await state.get_data()
    try:
        await data["prev_mess"].edit_text(data["prev_mess"].html_text)
    except:
        pass

    # Сохраняем данные
    title = message.text
    await state.update_data(title=title)

    # Меняем стейт
    await state.set_state(AddEventFSM.date)

    # Запрос даты
    msg = await message.answer("Введите дату в формате <b>ДД.ММ.ГГГГ</b> (например 25.07.2026)",
                               reply_markup=cancel_keyboard().as_markup())
    await state.update_data(prev_mess=msg)


@router.message(AddEventFSM.date)
async def get_date(message: Message, state: FSMContext):
    """Получение даты, запрос времени"""
    # Меняем предыдущее сообщение
    data = await state.get_data()
    try:
        await data["prev_mess"].edit_text(data["prev_mess"].html_text)
    except:
        pass

    # Если ввели неправильную дату
    date = message.text
    if not utils.is_valid_date(date):
        msg = await message.answer("Указан неверный формат даты\n\n"
                                   "Необходимо указать дату в формате <b>ДД.ММ.ГГГГ</b> без букв "
                                   "\"д\", \"м\" и \"г\" (например 25.07.2026)\n"
                                   "Дата не может быть раньше сегодняшней",
                                   reply_markup=cancel_keyboard().as_markup())
        await state.update_data(prev_mess=msg)
        return

    # Если дата правильная
    await state.update_data(date=date)
    await state.set_state(AddEventFSM.time)

    # Запрос времени
    msg = await message.answer("Введите время в формате <b>ММ:ЧЧ</b> (например 09:00)",
                               reply_markup=cancel_keyboard().as_markup())
    await state.update_data(prev_mess=msg)


@router.message(AddEventFSM.time)
async def get_time(message: Message, state: FSMContext):
    """Получение времени, запрос мест"""
    # Меняем предыдущее сообщение
    data = await state.get_data()
    try:
        await data["prev_mess"].edit_text(data["prev_mess"].html_text)
    except:
        pass

    # Если неправильное время
    time = message.text
    if not utils.is_valid_time(time):
        msg = await message.answer("Указан неверный формат времени\n\n"
                                   "Необходимо указать время в формате <b>ЧЧ:ММ</b> без букв \"м\" и \"ч\" "
                                   "(например 09:00 или 13:00)", reply_markup=cancel_keyboard().as_markup())
        await state.update_data(prev_mess=msg)
        return

    # Если время правильное
    await state.update_data(time=time)
    await state.set_state(AddEventFSM.places)

    # Запрос мест
    msg = await message.answer("Введите количество мест <b>цифрой</b>",
                               reply_markup=cancel_keyboard().as_markup())
    await state.update_data(prev_mess=msg)


@router.message(AddEventFSM.places)
async def get_places(message: Message, state: FSMContext):
    """Получение мест, запрос минимального количества мест"""
    # Меняем предыдущее сообщение
    data = await state.get_data()
    try:
        await data["prev_mess"].edit_text(data["prev_mess"].html_text)
    except:
        pass

    # Если неправильное количество мест
    places_str = message.text
    if not utils.is_valid_places(places_str):
        msg = await message.answer("Введено некорректное число\n\n"
                                   "Необходимо указать <b>число</b> без букв, знаков препинания и других символов "
                                   "(например 8, 16 или 24)", reply_markup=cancel_keyboard().as_markup())
        await state.update_data(prev_mess=msg)
        return

    # Если правильное количество мест
    await state.update_data(places=int(places_str))
    await state.set_state(AddEventFSM.min_count)

    # Запрос минимального количества мест
    msg = await message.answer("Введите <b>минимальное</b> необходимое количество участников для события",
                               reply_markup=cancel_keyboard().as_markup())
    await state.update_data(prev_mess=msg)


@router.message(AddEventFSM.min_count)
async def get_min_count(message: Message, state: FSMContext):
    """Получение минимального количества мест, запрос цены"""
    # Меняем предыдущее сообщение
    data = await state.get_data()
    try:
        await data["prev_mess"].edit_text(data["prev_mess"].html_text)
    except:
        pass

    # Если неправильное количество мин людей
    min_user_count_str = message.text
    if not utils.is_valid_places(min_user_count_str):
        msg = await message.answer("Введено некорректное число\n\n"
                                   "Необходимо указать <b>число</b> без букв, знаков препинания и других символов "
                                   "(например 2, 4 или 8)", reply_markup=cancel_keyboard().as_markup())
        await state.update_data(prev_mess=msg)
        return

    # Если правильное количество мин людей
    await state.update_data(min_user_count=int(min_user_count_str))
    await state.set_state(AddEventFSM.price)

    # Запрос минимального количества мест
    msg = await message.answer("Введите цифрой цену события", reply_markup=cancel_keyboard().as_markup())
    await state.update_data(prev_mess=msg)


@router.message(AddEventFSM.price)
async def get_price(message: Message, state: FSMContext, session: Any):
    """Получение цены сохранение события"""
    # Меняем предыдущее сообщение
    data = await state.get_data()
    try:
        await data["prev_mess"].edit_text(data["prev_mess"].html_text)
    except:
        pass

    # Если неправильная цена
    price_str = message.text
    if not utils.is_valid_price(price_str):
        msg = await message.answer("Введена некорректная цена\n\n"
                                   "Необходимо указать <b>число</b> без букв, знаков препинания и других символов "
                                   "(например 500, 1000 ил 1500)", reply_markup=cancel_keyboard().as_markup())
        await state.update_data(prev_mess=msg)
        return

    # Если правильная цена
    date_time_str = f"{data['date']} в {data['time']}"
    date_time = datetime.datetime.strptime(f"{data['date']} {data['time']}", "%d.%m.%Y %H:%M")

    # Создаем событие в БД
    event = AddEvent(
        type=data["type"],
        title=data["title"],
        date=date_time,
        places=data["places"],
        min_user_count=data["min_user_count"],
        active=True,
        price=int(price_str),
        level=None
    )

    try:
        event_id = await AsyncOrm.create_event(event, session)
        admin_tg_id = str(message.from_user.id)
        logger.info(f"Администратор {admin_tg_id} создал событие id {event_id}")

        await message.answer(f"Событие <b>\"{event.title}\"</b> <b>{date_time_str}</b> успешно создано ✅")
    except:
        await message.answer(f"Ошибка при создании события")

    await state.clear()
