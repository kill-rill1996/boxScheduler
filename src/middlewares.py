from collections.abc import Awaitable, Callable
from typing import Any

import asyncpg
from aiogram import BaseMiddleware, Bot
from aiogram.types import TelegramObject, CallbackQuery, Message

from src import buttons as btn
from database.orm import AsyncOrm
from settings import settings


class DatabaseMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        conn = await asyncpg.connect(
            user=settings.db.postgres_user,
            host=settings.db.postgres_host,
            password=settings.db.postgres_password,
            port=settings.db.postgres_port,
            database=settings.db.postgres_db
        )
        try:
            data["session"] = conn
            return await handler(event, data)
        finally:
            await conn.close()


class AdminMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        # Получаем сессию базы данных из контекста
        session: Any = data["session"]

        # проверяем есть ли бан у пользователя
        is_admin: bool = await self._check_user_is_admin(event, session)

        if is_admin:
            # Для администратора
            return await handler(event, data)

        # Для обычных пользователей
        else:
            # отправляем сообщение о блокировке
            bot: Bot = data["bot"]
            return await send_other_users_message(event, bot)


    async def _check_user_is_admin(self, event: TelegramObject, session: Any) -> bool:
        try:
            is_admin: bool = await AsyncOrm.user_is_admin(str(event.from_user.id), session)
            return is_admin
        except:
            return False     # в случае ошибок возвращаем False


async def send_other_users_message(event: CallbackQuery | Message, bot: Bot) -> None:
    """Сообщение для обычных пользователей"""
    await bot.send_message(event.from_user.id, f"{btn.INFO} Данный функционал доступен только администраторам", )