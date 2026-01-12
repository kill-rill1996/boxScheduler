from datetime import datetime

from database.schemas import Event
from settings import settings
import pytz


class FullnameException(Exception):
    """Ошибка валидации имени и фамилии"""
    pass

async def get_firstname_lastname(fullname: str) -> list[str]:
    """Проверка корректности введенного имени"""
    fullname_list = fullname.split(" ")
    try:
        firstname = fullname_list[0]
        lastname = fullname_list[1]
    except IndexError:
        raise FullnameException

    if len(fullname_list) != 2:
        raise FullnameException

    if len(firstname) < 2 or len(lastname) < 2:
        raise FullnameException

    for char in firstname:
        if char.isdigit() or not char.isalpha():
            raise FullnameException

    for char in lastname:
        if char.isdigit() or not char.isalpha():
            raise FullnameException

    return [firstname, lastname]


def get_weekday_from_date(date_str: str) -> str:
    """Получение дня недели из str даты в формате DD.MM.YYYY для использования в списке событий для пользователей"""
    date = datetime.strptime(date_str, "%d.%m.%Y").date()
    weekday = settings.weekdays[datetime.weekday(date)]
    return weekday


def get_active_dates(events: list[Event]) -> dict:
    """Формирование словаря с активными датами"""
    active_dates = {}

    for event in events:
        converted_date = event.date.strftime("%d.%m.%Y")

        if converted_date not in active_dates:
            active_dates[converted_date] = 1
        else:
            active_dates[converted_date] += 1

    return active_dates


def is_valid_date(date: str) -> bool:
    """Проверка валидности даты"""
    try:
        result = datetime.strptime(date, "%d.%m.%Y").date()
        if result < datetime.now(tz=pytz.timezone("Europe/Moscow")).date():
            return False
    except ValueError:
        return False
    return True


def is_valid_time(time: str) -> bool:
    """Проверка валидности времени"""
    time_list = time.split(":")

    if len(time_list) != 2:
        return False

    hours = time_list[0]
    minutes = time_list[1]
    try:
        hours = int(hours)
        minutes = int(minutes)
    except ValueError:
        return False

    if hours > 24 or hours < 0:
        return False
    if minutes > 59 or minutes < 0:
        return False

    return True


def is_valid_places(places: str) -> bool:
    """Проверка валидности количества мест"""
    try:
        places = int(places)
    except ValueError:
        return False

    if places <= 0:
        return False

    return True


def is_valid_price(price: str) -> bool:
    """Проверка валидности цены"""
    try:
        price = int(price)
    except ValueError:
        return False

    if price < 0:
        return False

    return True