from typing import Any

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from database.orm import AsyncOrm
from database.schemas import User
from src.messages import user_profile_message
from src.states import UpdateUser
from src.keyboards import cancel_keyboard, get_inline_keyboard
from src import utils

from settings import settings

router = Router()


# PROFILE
@router.callback_query(F.data == "profile")
async def profile(callback: CallbackQuery, session: Any):
    """Профиль пользователя"""
    await callback.answer()

    # Получаем пользователя
    tg_id = str(callback.from_user.id)
    user: User | None = await AsyncOrm.get_user_by_tg_id(tg_id, session)

    # Убеждаемся что есть такой пользователь
    if user:
        msg = user_profile_message(user)
        keyboard = get_inline_keyboard(
            {
                "📝 Изменить имя": "update_name",
            },
            back_callback="main_menu"
        )

        await callback.message.edit_text(msg, reply_markup=keyboard.as_markup())

    # При возникновении ошибки
    else:
        await callback.message.edit_text("Ошибка при получении данных профиля, повторите запрос позже")


# UPDATE PROFILE NAME
@router.callback_query(F.data == "update_name")
async def update_name(callback: CallbackQuery, state: FSMContext):
    """Начало изменения имени"""
    await callback.answer()

    await state.set_state(UpdateUser.name)
    msg = "Отправьте сообщением свои <b>имя</b> и <b>фамилию</b> (например Иван Иванов)."
    keyboard = cancel_keyboard()
    prev_mess = await callback.message.edit_text(msg, reply_markup=keyboard.as_markup())
    await state.update_data(prev_mess=prev_mess)


@router.message(UpdateUser.name)
async def get_name(message: Message, state: FSMContext, session: Any):
    """Получение и запись в БД имени"""
    data = await state.get_data()
    tg_id = str(message.from_user.id)

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

    await state.clear()

    # Обновляем данные в БД
    try:
        await AsyncOrm.update_user(firstname, lastname, tg_id, session)
        await message.answer("Данные успешно изменены ✅")

        # Возвращаем в профиль
        tg_id = str(message.from_user.id)
        user: User | None = await AsyncOrm.get_user_by_tg_id(tg_id, session)
        msg = user_profile_message(user)
        keyboard = get_inline_keyboard({"📝 Изменить имя": "update_name"}, back_callback="main_menu")

        await message.answer(msg, reply_markup=keyboard.as_markup())
    except Exception:
        await message.answer(f"Ошибка при изменении профиля, попробуйте позже или обратитесь к администратору "
                                         f"@{settings.admin_tg_username}")


