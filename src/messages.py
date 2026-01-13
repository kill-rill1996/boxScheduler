import datetime

from database.schemas import User, Event
from src import buttons as btn
from src.utils import convert_date_named_month, convert_time

from settings import settings

def main_menu_message() -> str:
    """Сообщение главного меню"""
    message = f"<b>Главное меню</b>\n\n" \
              f"<b>{btn.ALL_EVENTS}</b> - в этом разделе вы можете записаться на тренировку или игровой сбор.\n" \
              f"<b>{btn.PROFILE}</b> - в этом разделе вы можете изменить Фамилию, Имя. Узнать Ваш уровень игры.\n" \
              f"<b>{btn.MY_EVENTS}</b> - в этом разделе вы можете ознакомиться с событиями на которые вы записаны."
    return message


def user_profile_message(user: User) -> str:
    """Профиль пользователя"""
    gender_ru = "Мужской" if user.gender == "male" else "Женский"
    user_gender = f"👥 Пол: " + gender_ru if user.gender else f"👥 Пол: не указан"
    message = f"<b>Профиль</b>\n\n👤 {user.firstname} {user.lastname}\n{user_gender}"

    return message

def event_card(event: Event) -> str:
    """Карточка события"""
    date = convert_date_named_month(event.date)
    time = convert_time(event.date)
    weekday = settings.weekdays[datetime.datetime.weekday(event.date)]

    # user_registered_count = len(event.users_registered) TODO
    user_registered_count = 2

    message = f"📅 <b>{date}, {time} ({weekday})</b>\n"

    # Пользователь еще не регистрировался
    # if not payment: TODO
    #     pass
    payment = False

    # Пользователь ожидает подтверждения оплаты
    # elif not payment.paid_confirm: TODO
    #     message += "⏳ Ожидается подтверждение платежа от администратора\n\n"

    message += f"🥊 <b>\"{event.type}\"</b>\n" \
               f"  • {event.title}\n\n" \
               f"💰 <b>Стоимость участия:</b> {event.price} руб.\n" \
               f"👥 <b>Количество участников:</b> {user_registered_count}/{event.places} (доступно {event.places - user_registered_count} мест)\n" \
               f"⚠️ <b>Минимальное количество участников:</b> {event.min_user_count}\n" \
               f"📍 <b>Адрес:</b> <a href='{settings.address_url}'>{settings.address}</a>\n\n"

    # # если участники уже есть TODO
    # if event.users_registered:
    #     # сортировка по имени
    #     event.users_registered = sorted(event.users_registered, key=lambda user: user.firstname)
    #
    #     message += "<b>Участники:</b>\n"
    #     for idx, user in enumerate(event.users_registered, 1):
    #         message += f"<b>{idx}.</b> <a href='tg://user?id={user.tg_id}'>{user.firstname} {user.lastname}</a> " \
    #                    f"{f'({settings.levels[user.level]})' if user.level else ''}\n"
    #
    # # если есть резерв
    # if reserved_users:
    #     message += "\n<b>Резерв:</b>\n"
    #
    #     for idx, reserve in enumerate(reserved_users, 1):
    #         message += f"<b>{idx}.</b> <a href='tg://user?id={reserve.user.tg_id}'>{reserve.user.firstname} {reserve.user.lastname}</a> " \
    #                    f"{f'({settings.levels[reserve.user.level]})' if reserve.user.level else ''}\n"

    return message





