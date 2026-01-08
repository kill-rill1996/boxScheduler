import datetime

from pydantic import BaseModel


class AddUser(BaseModel):
    tg_id: str
    username: str | None
    firstname: str
    lastname: str
    level: str | None
    gender: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    is_banned: bool
    is_admin: bool