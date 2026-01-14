from pydantic import Field
from pydantic_settings import BaseSettings


CALENDAR_MONTHS = {
        1: "Январь",
        2: "Февраль",
        3: "Март",
        4: "Апрель",
        5: "Май",
        6: "Июнь",
        7: "Июль",
        8: "Август",
        9: "Сентябрь",
        10: "Октябрь",
        11: "Ноябрь",
        12: "Декабрь"
}


WEEKDAYS = {
    0: "Пн",
    1: "Вт",
    2: "Ср",
    3: "Чт",
    4: "Пт",
    5: "Сб",
    6: "Вс",
}

class Database(BaseSettings):
    postgres_user: str = Field()
    postgres_password: str = Field()
    postgres_db: str = Field()
    postgres_host: str = Field()
    postgres_port: str = Field()

    @property
    def DATABASE_URL(self):
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"


class Settings(BaseSettings):
    bot_token: str = Field()
    admins: list = Field()
    admin_tg_username: str = Field()
    admin_tg_id: str = Field()
    admin_phone: str = Field()

    # admin panel
    secret_key: str = Field()
    username: str = Field()
    password: str = Field()
    domain: str = Field()

    # events
    show_days: int = 10
    weekdays: dict = WEEKDAYS
    address_url: str = "https://yandex.ru/navi/org/volleyball_city/9644230187/?ll=30.333934%2C59.993168&z=16"
    address: str = "Санкт-Петербург, Институтский пер., 5Н"

    timezone: str = "Europe/Moscow"

    db: Database = Database()

    @property
    def calendar_months(self):
        return CALENDAR_MONTHS

settings = Settings()