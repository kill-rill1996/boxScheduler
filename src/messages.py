import datetime

from database.schemas import User, Event, EventUsers, Payment
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

def event_card(event: EventUsers, payment: Payment | None, for_admin: bool = False) -> str:
    """Карточка события"""
    date = convert_date_named_month(event.date)
    time = convert_time(event.date)
    weekday = settings.weekdays[datetime.datetime.weekday(event.date)]

    user_registered_count = len(event.users)

    message = f"📅 <b>{date}, {time} ({weekday})</b>\n"

    # Пользователь еще не регистрировался
    if not payment:
        pass

    # Пользователь ожидает подтверждения оплаты
    elif not payment.paid_confirm:
        message += "⏳ Ожидается подтверждение платежа от администратора\n\n"

    # Проверка статуса регистрации на событие
    else:
        # Пользователь зарегистрирован на событие
        if payment.user_id in [user.id for user in event.users]:
            message += f"✅ <b>Вы записаны на событие \"{event.type}\"</b>\n\n"
        # Пользователь зарегистрирован в резерв
        elif payment.user_id in [user.id for user in event.reserved]:
            message += f"📝 <b>Вы записаны в резерв на событие \"{event.type}\"</b>\n\n"

    message += f"🥊 <b>\"{event.type}\"</b>\n" \
               f"  • {event.title}\n\n" \
               f"💰 <b>Стоимость участия:</b> {event.price} руб.\n" \
               f"👥 <b>Количество участников:</b> {user_registered_count}/{event.places} (доступно {event.places - user_registered_count} мест)\n" \
               f"⚠️ <b>Минимальное количество участников:</b> {event.min_user_count}\n" \
               f"📍 <b>Адрес:</b> <a href='{settings.address_url}'>{settings.address}</a>\n\n"

    # # если участники уже есть
    if event.users:
        message += "<b>Участники:</b>\n"

        for idx, user in enumerate(event.users, 1):
            # Для админа
            if for_admin:
                message += f"<b>{idx}.</b> <a href='tg://user?id={user.tg_id}'>{user.firstname} {user.lastname}</a>\n"
            # Для пользователей
            else:
                message += f"<b>{idx}.</b> {user.firstname} {user.lastname}\n"

    # если есть резерв
    if event.reserved:
        message += "\n<b>Резерв:</b>\n"

        for idx, reserve_user in enumerate(event.reserved, 1):
            # Для админа
            if for_admin:
                message += f"<b>{idx}.</b> <a href='tg://user?id={reserve_user.tg_id}'>{reserve_user.firstname} {reserve_user.lastname}</a> " \
                           f"{f'({settings.levels[reserve_user.level]})' if reserve_user.level else ''}\n"
            # Для пользователей
            else:
                message += f"<b>{idx}.</b> {reserve_user.firstname} {reserve_user.lastname}\n"

    return message


def invoice_message_for_user(event: EventUsers, to_reserve: bool = False) -> str:
    """Сообщение о стоимости события"""
    date = convert_date_named_month(event.date)
    time = convert_time(event.date)
    message = ""

    # Если идет запись в резерв
    if to_reserve:
        message += f"📝 После оплаты вы будете записаны в <b>резерв</b>, если кто-то из участников отменит запись, вы автоматически будете добавлены в список участников события\n\n"

    message += f"🗓 <b>Дата и время:</b> {date}, {time}\n" \
               f"📅 <b>Событие:</b> {event.type}\n"\
               f"💰 <b>Стоимость участия:</b> {event.price} руб.\n\n"\
               f"Для записи на событие необходимо перевести {event.price} руб. на указанный номер телефона: <b>{settings.admin_phone} (Т-Банк)</b>\n\n"\
               f"❗<b>ВАЖНО:</b> \n" \
               f"📩 После оплаты, пожалуйста, отправьте чек в Telegram на @Bagration178, указав следующие данные: фамилия, имя и Ваш игровой уровень!\n\n" \
               f"После завершения оплаты нажмите кнопку <b>\"Оплатил(а)\".</b>"
    return message




