from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


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
    postgres_user: str = Field(..., env='POSTGRES_USER')
    postgres_password: str = Field(..., env='POSTGRES_USER')
    postgres_db: str = Field(..., env='POSTGRES_DB')
    postgres_host: str = Field(..., env='POSTGRES_HOST')
    postgres_port: str = Field(..., env='POSTGRES_PORT')

    @property
    def DATABASE_URL(self):
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"


class Settings(BaseSettings):
    bot_token: str = Field(..., env='BOT_TOKEN')
    admins: list = Field(..., env='ADMINS')
    admin_tg_username: str = Field(..., env='ADMIN_TG_USERNAME')

    # admin panel
    secret_key: str = Field(..., env='SECRET_KEY')
    username: str = Field(..., env='USERNAME')
    password: str = Field(..., env='PASSWORD')
    domain: str = Field(..., env='DOMAIN')

    timezone: str = "Europe/Moscow"

    db: Database = Database()

    @property
    def calendar_months(self):
        return CALENDAR_MONTHS

settings = Settings()