import asyncio

from aiogram.types import BotCommand, BotCommandScopeDefault

import aiogram as io
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from src.middlewares import DatabaseMiddleware
from settings import settings
from logger import logger
from src.routers import main_router



async def set_commands(bot: io.Bot):
    """Перечень команд для бота"""
    commands = [
        BotCommand(command="menu", description="👨🏻‍💻 Главное меню"),
        BotCommand(command="players", description="👥 Игроки"),
        BotCommand(command="help", description="❓ Инструкция и поддержка"),
        BotCommand(command="add_event", description="📌 Добавить событие"),
        BotCommand(command="events", description="⚙️ Управление событиями"),
    ]
    await bot.set_my_commands(commands, BotCommandScopeDefault())

#
async def set_description(bot: io.Bot):
    """Описание бота до запуска"""
    await bot.set_my_description("🥊 Бот предоставляет функционал записи на боксерские мероприятия\n\n"
                                 "Для запуска нажмите \"Начать\"")


async def start_bot() -> None:
    """Запуск бота"""
    bot = io.Bot(settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await set_commands(bot)
    await set_description(bot)

    storage = MemoryStorage()
    dp = io.Dispatcher(storage=storage)

    # ROUTERS
    dp.include_router(main_router)
    #
    # # MIDDLEWARES
    dp.message.middleware(DatabaseMiddleware())
    dp.callback_query.middleware(DatabaseMiddleware())

    # await AsyncOrm.create_tables()

    await dp.start_polling(bot)


if __name__ == "__main__":
    logger.info("Bot started")
    asyncio.run(start_bot())
