import datetime

import aiogram
import asyncpg
import pytz

from database.orm import AsyncOrm
from database.schemas import EventUsersIds, Event, User
from src import messages as ms, utils
from settings import settings


async def run_every_day(bot: aiogram.Bot):
    """Запуск ежедневной проверки"""
    session = await asyncpg.connect(
        user=settings.db.postgres_user,
        host=settings.db.postgres_host,
        password=settings.db.postgres_password,
        port=settings.db.postgres_port,
        database=settings.db.postgres_db
    )

    await notify_users_about_events(bot, session)   # напоминание о событиях
    await delete_old_events(session)    # удаление старых событий


async def run_every_hour(bot: aiogram.Bot) -> None:
    """Выполняется каждый час"""
    session = await asyncpg.connect(
        user=settings.db.postgres_user,
        host=settings.db.postgres_host,
        password=settings.db.postgres_password,
        port=settings.db.postgres_port,
        database=settings.db.postgres_db
    )

    await update_events(bot, session)
    await check_min_users_count(bot, session)


async def notify_users_about_events(bot: aiogram.Bot, session):
    """Напоминание пользователям о событиях, на которое они записались (за день до события)"""
    tomorrow_date = datetime.datetime.now() + datetime.timedelta(days=1)

    # Получаем события на завтрашний день
    events: list[EventUsersIds] = await AsyncOrm.get_events_by_date_with_users(tomorrow_date, session)

    # Проходим по событиям
    for event in events:
        for user_id in event.registered_users:
            # Получаем зарегистрированного пользователя
            user_tg_id = await AsyncOrm.get_user_tg_id(user_id, session)

            # Отправляем сообщение пользователю
            try:
                msg = ms.notify_user_about_event(event)
                await bot.send_message(user_tg_id, msg)
            except:
                pass

async def delete_old_events(session):
    """Удаление старых событий"""
    await AsyncOrm.delete_old_events(settings.delete_old_events_days, session)

async def update_events(bot: aiogram.Bot, session):
    """Обновление статуса событий (active True/False) и оповещения администратора о возврате средств"""
    # Получаем все события
    events: list[Event] = await AsyncOrm.get_events(session, only_active=True)

    # Проверяем прошло ли событие
    # TODO Перевод в москвоское время
    current_date = datetime.datetime.now()

    for event in events:
        if current_date > event.date:
            # Меняем статус события на неактивное
            await AsyncOrm.event_change_to_inactivity(event.id, session)
            # Получаем резервных пользователей для события
            reserved_users: list[User] = await AsyncOrm.get_reserved_users(event.id, session)

            # отправляем администратору список людей резерва, для возвращения оплаты
            if reserved_users:
                date = utils.convert_date(event.date)
                time = utils.convert_time(event.date)
                msg_for_admin = f"Необходимо вернуть деньги следующим <b>пользователям из резерва</b> " \
                                f"на событие {event.type} \"{event.title}\" {date} в {time}:\n\n"

                for user in reserved_users:
                    msg_for_admin += f"<a href='tg://user?id={user.user.tg_id}'>{user.user.firstname} {user.user.lastname}</a> - {event.price} руб.\n"

                # отправляем сообщение администратору
                try:
                    await bot.send_message(settings.admin_tg_id, msg_for_admin)
                except:
                    pass

async def check_min_users_count(bot: aiogram.Bot, session):
    """Проверка необходимого кол-ва участников на событие"""
    current_date = datetime.datetime.now()

    # Получаем ближайшие события
    events: list[EventUsersIds] = await AsyncOrm.get_events_by_date_with_users(current_date, session)

    for event in events:
        # Если недостаточно зарегистрированных пользователей
        if len(event.registered_users) <= event.min_user_count:

            # Переводим мероприятие в неактивные
            await AsyncOrm.event_change_to_inactivity(event.id, session)

            # Оповещаем зарегистрированных пользователей
            msg = ms.notify_canceled_event(event)
            for user_id in event.registered_users:
                # Получаем tg_id пользователя
                user_tg_id = await AsyncOrm.get_user_tg_id(user_id, session)
                # Отправляем сообщение
                try:
                    await bot.send_message(user_tg_id, msg)
                except:
                    pass

