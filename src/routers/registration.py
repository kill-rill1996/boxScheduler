import datetime
from typing import Any

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from database.orm import AsyncOrm
from database.schemas import AddUser
from src.routers.menu import main_menu
from src.states import Registration
from src.keyboards import cancel_keyboard, get_inline_keyboard
from src import utils

from settings import settings

router = Router()

@router.message(Registration.name)
async def start(message: Message, state: FSMContext):
    """Получение имени от пользователя при регистрации"""
    data = await state.get_data()

    # Убираем клавиатуру у сообщения
    try:
        await data["prev_mess"].edit_text(data["prev_mess"].html_text)
    except Exception:
        pass

    # Проверяем что отправлен текст
    if not message.text:
        prev_mess = await message.answer("Неверный формат данных, необходимо отправить текст",
                                         reply_markup=cancel_keyboard().as_markup())
        # Сохраняем предыдущее сообщение
        await state.update_data(prev_mess=prev_mess)
        return

    # Проверяем корректность введнных данных
    try:
        firstname, lastname = await utils.get_firstname_lastname(message.text)

    # ошибка введения данных
    except utils.FullnameException:
        prev_mess = await message.answer(
            "Необходимо ввести <b>имя и фамилию через пробел</b> без знаков препинания, символов "
            "и цифр (например Иван Иванов)",
            reply_markup=cancel_keyboard().as_markup()
        )
        # Сохраняем предыдущее сообщение
        await state.update_data(prev_mess=prev_mess)
        return

    # Сохраняем корректные данные
    await state.update_data(firstname=firstname, lastname=lastname)

    # Меняем state
    await state.set_state(Registration.gender)

    keyboard = get_inline_keyboard(
        {
            "Мужской": "male",
            "Женский": "female",
        },
        cancel_button=True
    )
    await message.answer("Выберите пол", reply_markup=keyboard.as_markup())

@router.callback_query(Registration.gender)
async def get_gender(callback: CallbackQuery, session: Any, state: FSMContext):
    """Получаем выбранный пол"""
    await callback.answer()

    data = await state.get_data()
    gender = callback.data
    created_at = datetime.datetime.now()

    # скидываем state
    await state.clear()

    # Создаем модель User
    new_user = AddUser(
        tg_id=str(callback.from_user.id),
        username=callback.from_user.username,
        firstname=data['firstname'],
        lastname=data['lastname'],
        level=None,
        gender=gender,
        created_at=created_at,
        updated_at=created_at,
        is_banned=False,
        is_admin=False
    )

    # Записываем пользователя в БД
    try:
        await AsyncOrm.create_user(new_user, session)
    except:
        await callback.message.edit_text(f"Ошибка при регистрации, попробуйте позже или обратитесь к администратору "
                                         f"@{settings.admin_tg_username}")
        return

    # Перенаправляем пользователя в главное меню
    await callback.message.edit_text("Вы успешно зарегистрированы ✅")
    await main_menu(callback)


