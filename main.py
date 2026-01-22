import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram.types import BotCommand, BotCommandScopeDefault

import aiogram as io
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from datetime import datetime

from src.middlewares import DatabaseMiddleware
from settings import settings
from logger import logger
from src.routers import main_router
from src import buttons as btn, schedulers



async def set_commands(bot: io.Bot):
    """Перечень команд для бота"""
    commands = [
        BotCommand(command="menu", description=f"{btn.MAIN_MENU}"),
        BotCommand(command="players", description=f"{btn.PLAYERS}"),
        BotCommand(command="help", description=f"{btn.HELP}"),
        BotCommand(command="add_event", description=f"{btn.ADD_EVENT}"),
        BotCommand(command="events", description=f"{btn.MANAGE_EVENT}"),
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

    # SCHEDULER
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")

    # оповещение для пользователей + удаление старых неактивных событий 9 утра
    scheduler.add_job(schedulers.run_every_day, trigger="cron", year='*', month='*', day="*", hour=9, minute=0,
                      second=0, start_date=datetime.now(), kwargs={"bot": bot})

    # проверка мероприятия на минимальное кол-во участников + перевод событий в неактивные
    scheduler.add_job(schedulers.run_every_hour, trigger="cron", year='*', month='*', day="*", hour="*", minute=1,
                      second=0, start_date=datetime.now(), kwargs={"bot": bot})

    # # создание excel файла
    # scheduler.add_job(apsched.create_players_excel, trigger="cron", year='*', month='*', day="*", hour="*",
    #                   minute="*/10",
    #                   second=0, start_date=datetime.now())

    scheduler.start()

    # ROUTERS
    dp.include_router(main_router)

    # MIDDLEWARES
    dp.message.middleware(DatabaseMiddleware())
    dp.callback_query.middleware(DatabaseMiddleware())

    # await AsyncOrm.create_tables()

    await dp.start_polling(bot)


if __name__ == "__main__":
    logger.info("Bot started")
    asyncio.run(start_bot())
