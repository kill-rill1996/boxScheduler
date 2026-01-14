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


class User(AddUser):
    id: int


class AddEvent(BaseModel):
    type: str
    title: str
    date: datetime.datetime
    places: int
    min_user_count: int
    active: bool
    level: int | None = None
    price: int


class Event(AddEvent):
    id: int


class EventUsers(Event):
    users: list[User] = []
    reserved: list[User] = []


class AddPayment(BaseModel):
    paid: bool
    paid_confirm: bool
    user_id: int
    event_id: int


class Payment(AddPayment):
    id: int
