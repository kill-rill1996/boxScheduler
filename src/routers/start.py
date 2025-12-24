from aiogram import Router, types, F, Bot
from aiogram.filters import Command

router = Router()

@router.message(Command(f"start"))
async def start(message: types.Message) -> None:
    """Старт хендлер"""
    await message.answer("Hello")