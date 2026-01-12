import datetime
from collections.abc import Mapping
from typing import Any, List

import asyncpg

from database.database import async_engine
from database.schemas import AddUser, User, Event
from database.tables import Base

from logger import logger
from settings import settings

# для model_validate регистрируем возвращаемый из asyncpg.fetchrow класс Record
Mapping.register(asyncpg.Record)


class AsyncOrm:

    @staticmethod
    async def create_tables():
        """Создание таблиц"""
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    @staticmethod
    async def drop_tables():
        """Удаление таблиц"""
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)


    @staticmethod
    async def is_registered(tg_id: str, session: Any) -> bool:
        """Проверка регистрации"""
        try:
            exists = await session.fetchval(
                """
                SELECT EXISTS(SELECT 1 FROM users WHERE tg_id = $1)
                """,
                tg_id,
            )
            return exists

        except Exception as e:
            logger.error(f"Ошибка при проверке регистрации: {e}")

    @staticmethod
    async def create_user(user: AddUser, session: Any) -> None:
        """Создание нового пользователя"""
        try:
            await session.execute(
                """
                INSERT INTO users (tg_id, username, firstname, lastname, level, gender, created_at, updated_at, is_banned, is_admin)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                """,
                user.tg_id, user.username, user.firstname, user.lastname, user.level, user.gender,
                user.created_at, user.updated_at, user.is_banned, user.is_admin
            )
        except Exception as e:
            logger.error(f"Ошибка при создании пользователя {user.tg_id}: {e}")
            raise

    @staticmethod
    async def update_user(firstname: str, lastname: str, tg_id: str, session: Any) -> None:
        """Изменение имени профиля"""
        try:
            await session.execute(
                """
                UPDATE users
                SET firstname = $1, lastname = $2
                WHERE tg_id = $3
                """,
                firstname, lastname, tg_id
            )
        except Exception as e:
            logger.error(f"Ошибка при изменении имени профиля пользователя {tg_id} на {firstname} {lastname}: {e}")
            raise

    @staticmethod
    async def get_user_by_tg_id(tg_id: str, session: Any) -> User | None:
        """Получение пользователя по tg_id"""
        try:
            row = await session.fetchrow(
                """
                SELECT *
                FROM users
                WHERE tg_id = $1
                """,
                tg_id
            )
            if row:
                return User.model_validate(row)
            else:
                return None
        except Exception as e:
            logger.error(f"Ошибка при получение пользователя tg_id {tg_id}: {e}")

    @staticmethod
    async def get_upcoming_events(session: Any, only_active: bool = True) -> list[Event] | None:
        """Получает события на ближайшие N дней"""
        now = datetime.datetime.today()
        deadline = datetime.datetime.now() + datetime.timedelta(days=settings.show_days)

        try:
            rows = await session.fetch(
                """
                SELECT * FROM events
                WHERE date >= $1 AND date <= $2
                ORDER BY date
                """,
                now, deadline
            )

            events = []
            for row in rows:
                # Пропускаем неактивные при необходимости
                if only_active and row["active"] == False:
                    continue

                events.append(Event.model_validate(row))

            return events

        except Exception as e:
            logger.error(f"Ошибка при получение ближайших событий: {e}")
