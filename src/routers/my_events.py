import datetime
from typing import Any

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

import logger
from database.orm import AsyncOrm
from database.schemas import User, EventUsers, EventUsersPayment
from src.messages import user_profile_message
from src.routers.menu import main_menu
from src.states import Registration, UpdateUser
from src.keyboards import cancel_keyboard, get_inline_keyboard
from src import utils

from settings import settings
from logger import logger

router = Router()


@router.callback_query(F.data == "my_events")
async def my_events_list(callback: CallbackQuery, session: Any):
    """Мои события"""
    tg_id = str(callback.from_user.id)

    # Получаем пользователя
    user: User = await AsyncOrm.get_user_by_tg_id(tg_id, session)

    # Получаем события пользователя
    events: list[EventUsersPayment] = await AsyncOrm.get_events_for_user(user.id, session)

