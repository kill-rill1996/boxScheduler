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

    # admin panel
    secret_key: str = Field()
    username: str = Field()
    password: str = Field()
    domain: str = Field()

    timezone: str = "Europe/Moscow"

    db: Database = Database()

    @property
    def calendar_months(self):
        return CALENDAR_MONTHS

settings = Settings()