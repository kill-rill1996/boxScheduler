from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, FSInputFile

from logger import logger


router = Router()


@router.message(Command("users"))
async def send_excel_all_users(message: Message):
    """Получение excel файла со всеми пользователями"""
    wait_msg = await message.answer("⏳ Запрос выполняется...")
    try:
        document = FSInputFile('players/users.xlsx')
        await wait_msg.delete()
        await message.answer_document(document)
    except Exception as e:
        logger.error(f"Не получилось отправить user.xlsx пользователю {message.from_user.id}: {e}")