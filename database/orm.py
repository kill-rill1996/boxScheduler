import datetime
from collections.abc import Mapping
from typing import Any, List

import asyncpg

from database.database import async_engine
from database.schemas import AddUser, User, AddEvent, Event, EventUsers, Payment, AddPayment, EventUsersPayment, \
    EventUsersIds
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
    async def get_user_by_id(user_id: int, session: Any) -> User | None:
        """Получение пользователя по id"""
        try:
            row = await session.fetchrow(
                """
                SELECT *
                FROM users
                WHERE id = $1
                """,
                user_id
            )
            if row:
                return User.model_validate(row)
            else:
                return None
        except Exception as e:
            logger.error(f"Ошибка при получение пользователя id {user_id}: {e}")

    @staticmethod
    async def get_user_tg_id(user_id: int, session: Any) -> str | None:
        """Получение tg_id пользователя"""
        try:
            tg_id = await session.fetchval(
                """
                SELECT tg_id FROM users
                WHERE id = $1
                """,
                user_id
            )
            return tg_id

        except Exception as e:
            logger.error(f"Ошибка при получении tg_id пользователя id '{user_id}': {e}")
            
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
    async def get_events(session: Any, only_active: bool = False) -> List[Event] | None:
        """Получение событий активных/всех"""
        try:
            if only_active:
                rows = await session.fetch(
                    """
                    SELECT *
                    FROM events
                    WHERE active = true
                    ORDER BY date
                    """
                )
            else:
                rows = await session.fetch(
                    """
                    SELECT *
                    FROM events
                    ORDER BY date
                    """
                )
            events = [Event.model_validate(row) for row in rows]
            return events
        except Exception as e:
            logger.error(f"Ошибка при получении всех событий: {e}")

    @staticmethod
    async def delete_old_events(days_passed: int, session: Any) -> None:
        """Удаление старых события по истечению N дней"""
        expire_date = datetime.datetime.now() - datetime.timedelta(days=days_passed)

        try:
            await session.execute(
                """
                DELETE FROM events
                WHERE date < $1 
                """,
                expire_date
            )
            logger.info(f"Удалены события с датой раньше чем {expire_date}")

        except Exception as e:
            logger.error(f"Ошибка при удалении старых событий: {e}")

    @staticmethod
    async def event_change_to_inactivity(event_id: int, session: Any) -> None:
        """Изменение статуса события на неактивное"""
        try:
            await session.execute(
                """
                UPDATE events
                SET active = false
                WHERE id = $1
                """,
                event_id
            )
            logger.info(f"Событие {event_id} переведено в неактивное")

        except Exception as e:
            logger.error(f"Ошибка при изменении статуса события {event_id} на неактивное:{e}")


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
    async def get_events_by_date_with_users(date: datetime.datetime, session: Any) -> list[EventUsersIds] | None:
        """Получение событий по дате с записанными и резервными пользователями"""
        min_date = datetime.datetime.combine(date, datetime.datetime.min.time())
        max_date = min_date + datetime.timedelta(days=1)
        logger.info(f"min date {min_date}, max_date {max_date}")

        try:
            rows = await session.fetch(
                """
                SELECT e.*,
                    COALESCE(
                        ARRAY_AGG(DISTINCT eu.user_id) FILTER (WHERE eu.user_id IS NOT NULL),
                        ARRAY[]::integer[]
                    ) as registered_users,
                    COALESCE(
                        ARRAY_AGG(DISTINCT r.user_id) FILTER (WHERE r.user_id IS NOT NULL),
                        ARRAY[]::integer[]
                    ) as reserved_users
                FROM events e
                LEFT JOIN events_users eu ON e.id = eu.event_id
                LEFT JOIN reserved r ON e.id = r.event_id
                WHERE e.date >= $1 AND e.date <= $2 AND e.active = true
                GROUP BY e.id
                ORDER BY e.date
                """,
                min_date, max_date
            )
            events = [EventUsersIds.model_validate(row) for row in rows]
            return events

        except Exception as e:
            logger.error(f"Ошибка при получений событий за {date} с пользователями (основными и резервными): {e}")


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

    @staticmethod
    async def get_event_with_users(event_id: int, session: Any) -> EventUsers:
        """Получение события с пользователями и резервом"""
        try:
            event_row = await session.fetchrow(
                """
                SELECT * FROM events 
                WHERE id = $1
                """,
                event_id
            )
            event: EventUsers = EventUsers.model_validate(event_row)

            # Получение пользователей в событии
            users_rows = await session.fetch(
                """
                SELECT u.* 
                FROM users AS u
                JOIN events_users AS eu ON eu.user_id = u.id
                WHERE eu.event_id = $1
                ORDER BY u.firstname
                """,
                event_id
            )
            users = [User.model_validate(row) for row in users_rows]
            event.users = users

            # Получение резерва для события
            reserved_rows = await session.fetch(
                """
                SELECT u.* 
                FROM users AS u
                JOIN reserved AS r ON r.user_id = u.id
                WHERE r.event_id = $1
                ORDER BY r.created_at ASC
                """,
                event_id
            )
            event.reserved = [User.model_validate(row) for row in reserved_rows]
            return event

        except Exception as e:
            logger.error(f"Ошибка при получении события {event_id} с пользователями: {e}")

    @staticmethod
    async def get_events_for_user(user_id: int, session: Any) -> List[EventUsersPayment]:
        """Получение мероприятий пользователя"""
        try:
            # Получаем основные события
            events_rows = await session.fetch(
                """
                SELECT e.*
                FROM events AS e
                JOIN events_users AS eu ON e.id = eu.event_id
                JOIN payments AS p ON e.id = p.event_id
                WHERE eu.user_id = $1 AND e.active = true
                ORDER BY e.date ASC
                """,
                user_id
            )
            events = [EventUsersPayment.model_validate(row) for row in events_rows]

            # Получаем резервные события пользователя
            reserved_rows = await session.fetch(
                """
                SELECT e.*
                FROM events AS e
                JOIN reserved AS r ON e.id = r.event_id
                JOIN payments AS p ON e.id = p.event_id
                WHERE r.user_id = $1 AND e.active = true
                ORDER BY e.date ASC
                """,
                user_id
            )
            reserved = [EventUsersPayment.model_validate(row) for row in reserved_rows]

            # Сортируем все события
            all_events = events + reserved
            all_events = sorted(all_events, key=lambda event: event.date)

            # Получаем платеж, участников события и резервы для события
            for e in all_events:
                # Платеж
                payment_row = await session.fetchrow(
                    """
                    SELECT * 
                    FROM payments
                    WHERE user_id = $1 AND event_id = $2
                    """,
                    user_id, e.id
                )
                payment = Payment.model_validate(payment_row)
                e.payment = payment

                # Участники
                users_rows = await session.fetch(
                    """
                    SELECT u.*
                    FROM users AS u
                    JOIN events_users AS eu ON eu.user_id = u.id
                    WHERE eu.event_id = $1
                    ORDER BY u.firstname
                    """,
                    e.id
                )
                users = [User.model_validate(row) for row in users_rows]
                e.users = users

                # Резерв
                reserved_users_rows = await session.fetch(
                    """
                    SELECT u.*
                    FROM users AS u
                    JOIN reserved AS r ON r.user_id = u.id
                    WHERE r.event_id = $1
                    ORDER BY r.created_at ASC
                    """,
                    e.id
                )
                reserved_users = [User.model_validate(row) for row in reserved_users_rows]
                e.reserved = reserved_users

            return all_events
        except Exception as e:
            logger.error(f"Ошибка при получении событий пользователя с платежами {user_id}: {e}")

    @staticmethod
    async def delete_user_from_event(event_id: int, user_id: int, session: Any) -> None:
        """Удаление пользователя с события"""
        try:
            await session.execute(
                """
                DELETE FROM events_users
                WHERE event_id = $1 AND user_id = $2
                """,
                event_id, user_id
            )
            logger.info(f"Пользователь id {user_id} удален с события id {event_id}")
        except Exception as e:
            logger.error(f"Ошибка при удалении пользователя id {user_id} с события id {event_id}: {e}")
            raise

    @staticmethod
    async def get_reserved_users(event_id: int, session: Any) -> list[User]:
        """Получение резервных пользователей на событие"""
        try:
            rows = await session.fetch(
                """
                SELECT u.*
                FROM reserved AS r
                JOIN users AS u ON r.user_id = u.id
                WHERE r.event_id = $1
                """,
                event_id
            )
            users = [User.model_validate(row) for row in rows]
            return users

        except Exception as e:
            logger.error(f"Ошибка при получение резервных пользователей для события {event_id}: {e}")

    @staticmethod
    async def transfer_user_from_reserve(event_id: int, user_id: int, session: Any) -> None:
        """Перемещение пользователя из резерва в основу"""
        pass

    @staticmethod
    async def get_payment(tg_id: str, event_id: int, session: Any) -> Payment | None:
        """Получение платежа пользователя на событие"""
        try:
            row = await session.fetchrow(
                """
                SELECT u.*
                FROM payments AS p
                JOIN users AS u ON p.user_id = u.id
                WHERE u.tg_id = $1 AND p.event_id = $2 
                """,
                tg_id, event_id
            )
            if row:
                return Payment.model_validate(row)
            return None

        except Exception as e:
            logger.error(f"Ошибка при получении платежа пользователя tg_id {tg_id} на событие {event_id}: {e}")

    @staticmethod
    async def create_payment(payment: AddPayment, session: Any) -> None:
        """Создание платежа"""
        try:
            await session.execute(
                """
                INSERT INTO payments (user_id, event_id, paid, paid_confirm)
                VALUES ($1, $2, $3, $4)
                """,
                payment.user_id, payment.event_id, payment.paid, payment.paid_confirm
            )
            logger.info(f"Создан платеж пользователя id {payment.user_id} на событие {payment.event_id}")
        except Exception as e:
            logger.error(f"Ошибка создания платежа пользователя id {payment.user_id} на событие {payment.event_id}: {e}")
            raise

    @staticmethod
    async def update_payment_status(event_id: int, user_id: int, session: Any) -> None:
        """Обновление статуса платежа"""
        try:
            await session.execute(
                """
                UPDATE payments
                SET paid_confirm = true
                WHERE event_id = $1 AND user_id = $2
                """,
                event_id, user_id
            )
            logger.info(f"Статус платежа пользователя {user_id} на событие {event_id} изменен на true")
        except Exception as e:
            logger.error(f"Ошибка при изменении статуса платежа пользователя {user_id} на событие {event_id}: {e}")
            raise

    @staticmethod
    async def delete_payment(event_id: int, user_id: int, session: Any) -> None:
        """Удаление платежа"""
        try:
            await session.execute(
                """
                DELETE FROM payments
                WHERE event_id = $1 AND user_id = $2
                """,
                event_id, user_id
            )
            logger.info(f"Платеж пользователя {user_id} на событие {event_id} удален")
        except Exception as e:
            logger.error(f"Ошибка при удалении платежа пользователя {user_id} на событие {event_id}: {e}")

    @staticmethod
    async def create_reserve(event_id: int, user_id: int, session: Any) -> None:
        """Создание записи в резерве"""
        try:
            created_at = datetime.datetime.now()

            await session.execute(
                """
                INSERT INTO reserved (event_id, user_id, created_at)
                VALUES ($1, $2, $3)
                """,
                event_id, user_id, created_at
            )
            logger.info(f"Пользователь id {user_id} записан в резерв события {event_id}")
        except Exception as e:
            logger.error(f"Ошибка при записи пользователя id {user_id} в резерв события {event_id}: {e}")
            raise

    @staticmethod
    async def create_event_user(event_id: int, user_id: int, session: Any) -> None:
        """Создание events_users"""
        try:
            created_at = datetime.datetime.now()

            await session.execute(
                """
                INSERT INTO events_users (event_id, user_id, created_at)
                VALUES ($1, $2, $3)
                """,
                event_id, user_id, created_at
            )
            logger.info(f"Пользователь id {user_id} записан в основу события {event_id}")
        except Exception as e:
            logger.error(f"Ошибка при записи пользователя id {user_id} в основу события {event_id}: {e}")
            raise
