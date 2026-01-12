from database.schemas import User
from src import buttons as btn

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