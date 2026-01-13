import datetime
from collections.abc import Mapping
from typing import Any, List

import asyncpg

from database.database import async_engine
from database.schemas import AddUser, User, AddEvent, Event
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
    async def user_is_admin(tg_id: str, session: Any) -> bool:
        """Проверка администратора"""
        try:
            is_admin = await session.fetchval(
                """
                SELECT is_admin
                FROM users
                WHERE tg_id = $1
                """,
                tg_id
            )
            return is_admin
        except Exception as e:
            logger.error(f"Ошибка при проверка администратора {tg_id}: {e}")

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
            logger.info(f"Зарегистрирован пользователь {user.tg_id} {user.firstname} {user.lastname}")
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
            logger.info(f"Имя пользователя {tg_id} изменено на {firstname} {lastname}")
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
    async def create_event(event: AddEvent, session: Any) -> int:
        """Создание события"""
        try:
            event_id = await session.fetchval(
                """
                INSERT INTO events (type, title, date, places, min_user_count, active, level, price)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING id
                """,
                event.type, event.title, event.date, event.places, event.min_user_count, event.active, event.level,
                event.price
            )
            logger.info(f"Создано событие {event.type} {event.title} {event.date}")
            return event_id

        except Exception as e:
            logger.error(f"Ошибка при создании события {event.type} {event.title} {event.date}: {e}")
            raise

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

    @staticmethod
    async def get_events_by_date(date: datetime.datetime, session: Any, only_active: bool = True) -> list[Event] | None:
        min_date = datetime.datetime.combine(date, datetime.datetime.min.time())
        max_date = min_date + datetime.timedelta(days=1)

        try:
            rows = await session.fetch(
                """
                SELECT * FROM events
                WHERE date >= $1 AND date <= $2
                ORDER BY date
                """,
                min_date, max_date
            )
            events = []

            for row in rows:
                if only_active and row["active"] == False:
                    continue
                events.append(Event.model_validate(row))

            return events

        except Exception as e:
            logger.error(f"Ошибка при получений событий за {date}: {e}")

    @staticmethod
    async def get_event_by_id(event_id: int, session: Any) -> Event | None:
        """Получение события по id"""
        try:
            row = await session.fetchrow(
                """
                SELECT * FROM events WHERE id = $1
                """,
                event_id
            )

            return Event.model_validate(row)

        except Exception as e:
            logger.error(f"Ошибка при получении собыытия по id {event_id}: {e}")