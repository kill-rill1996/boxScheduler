from typing import Any

from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from database.orm import AsyncOrm
from .menu import main_menu
from src.states import Registration
from src.keyboards import cancel_keyboard

router = Router()

@router.message(Command("start"))
@router.message(Command("menu"))
async def start(message: types.Message, session: Any, state: FSMContext) -> None:
    """Старт хендлер"""
    tg_id = str(message.from_user.id)

    # Проверяем регистрацию
    registered: bool = await AsyncOrm.is_registered(tg_id, session)

    # Для зарегистрированных
    if registered:
        await main_menu(message)

    # Для новых пользователей
    else:
        await state.set_state(Registration.name)

        msg = await message.answer(
            "Для записи на спортивные события необходимо зарегистрироваться\n\n"
                 "Отправьте сообщением свои <b>имя</b> и <b>фамилию</b> (например Иван Иванов)",
            reply_markup=cancel_keyboard().as_markup(),
        )

        await state.update_data(prev_mess=msg)


@router.callback_query(F.data == "cancel")
async def cancel(callback: CallbackQuery, state: FSMContext) -> None:
    """Роутер для отмены и сброса state"""
    try:
        await state.clear()
        await callback.answer()
        await callback.message.delete()
    except:
        pass

