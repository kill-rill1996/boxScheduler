from typing import Any

from aiogram import Router, types, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from database.orm import AsyncOrm
from src.keyboards import main_menu_keyboard
from src.messages import main_menu_message

router = Router()

@router.callback_query(F.data == "main_menu")
async def main_menu(message: Message | CallbackQuery) -> None:
    """Главное меню"""
    msg = main_menu_message()
    keyboard = main_menu_keyboard()

    if isinstance(message, Message):
        await message.answer(msg, reply_markup=keyboard.as_markup())
    else:
        await message.answer()
        await message.message.edit_text(msg, reply_markup=keyboard.as_markup())