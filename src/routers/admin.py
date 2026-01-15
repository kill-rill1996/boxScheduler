from aiogram.filters import or_f
from typing import Any

from aiogram import Router, F
from aiogram.types import CallbackQuery

from database.orm import AsyncOrm
from database.schemas import EventUsers, User
from logger import logger
from settings import settings
from src import utils
from src.middlewares import AdminMiddleware
from src import buttons as btn


router = Router()
router.message.middleware.register(AdminMiddleware())
router.callback_query.middleware.register(AdminMiddleware())


# ПОДТВЕРЖДЕНИЕ И ОТКЛОНЕНИЕ ОПЛАТЫ
@router.callback_query(or_f(F.data.split("|")[0] == "admin-payment-reserve", F.data.split("|")[0] == "admin-payment"))
async def confirm_payment(callback: CallbackQuery, session: Any):
    """Начало создания события"""
    await callback.answer()

    status = callback.data.split("|")[1] # ok/cancel
    event_id = int(callback.data.split("|")[2])
    user_id = int(callback.data.split("|")[3])
    to_reserve = callback.data.split("|")[0] == "admin-payment-reserve"
    admin_msg = callback.message.html_text.split("\n\n")[0]

    # Получаем событие
    event: EventUsers = await AsyncOrm.get_event_with_users(event_id, session)
    user: User = await AsyncOrm.get_user_by_id(user_id, session)
    event_is_full = len(event.users) >= event.places

    try:
        # Подтверждение оплаты
        if status == "ok":
            # Обновляем статус платежа
            await AsyncOrm.update_payment_status(event_id, user_id, session)
            logger.info(f"Администратор {callback.from_user.id} подтвердил платеж пользователя {user_id} на событие {event_id}")

            # Запись в резерв
            if to_reserve:
                # Создаем запись в резерве
                await AsyncOrm.create_reserve(event_id, user_id, session)

            # Запись в основу
            else:
                # Если мест не осталось записвыаем в резерв
                if event_is_full:
                    await AsyncOrm.create_reserve(event_id, user_id, session)
                    to_reserve = True

                # Если есть места в основе
                else:
                    await AsyncOrm.create_event_user(event_id, user_id, session)

            # Подготовка сообщения админу
            if to_reserve:
                admin_msg += "\n\nОплата подтверждена ✅\nПользователь записан <b>в резерв</b>, так как свободных мест уже нет."
            else:
                admin_msg += "\n\nОплата подтверждена ✅\nПользователь записан на событие"

            # Подготовка сообщения пользователю
            date = utils.convert_date_named_month(event.date)
            time = utils.convert_time(event.date)
            if to_reserve:
                user_msg = f"🔔 <b>Автоматическое уведомление</b>\n\nОплата прошла успешно ✅\nВы <b>записаны в резерв</b> " \
                      f"на событие {event.type} \"{event.title}\" {date} в {time}, так как свободных мест пока нет"
            else:
                user_msg = f"🔔 <b>Автоматическое уведомление</b>\n\nОплата прошла успешно ✅\nВы записаны на {event.type} \"{event.title}\" {date} в {time}"

        # Отклоненеие оплаты
        else:
            # Удаление платежа
            await AsyncOrm.delete_payment(event_id, user_id, session)
            logger.info(f"Администратор {callback.from_user.id} отклонил платеж пользователя {user_id} на событие {event_id}")

            # Сообщение админу
            admin_msg += "Оплата отклонена ❌\nОповещение направлено пользователю"

            # Сообщение пользователю
            user_msg = f"🔔 <b>Автоматическое уведомление</b>\n\n❌ Администратор оплату не подтвердил\n" \
                  f"Вы можете связаться с администрацией канала @{settings.admin_tg_username}"

        # Отправка сообщения админу
        await callback.message.edit_text(admin_msg)

        # Отправка сообщения пользователю
        await callback.bot.send_message(user.tg_id, user_msg)

    except:
        await callback.message.edit_text(f"{btn.INFO} Произошла ошибка, попробуйте позже")
        return
