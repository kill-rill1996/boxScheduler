import datetime
from enum import Enum

from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped, relationship
from sqlalchemy import ForeignKey, String

class Level(Enum):
    BEGINNER = "Новичок"
    MEDIUM = "Любитель"
    PROFESSIONAL = "Профессионал"


class Base(DeclarativeBase):
    repr_cols_num = 3
    repr_cols = tuple()

    def __repr__(self):
        cols = []
        for idx, col in enumerate(self.__table__.columns.keys()):
            if col in self.repr_cols or idx < self.repr_cols_num:
                cols.append(f"{col}={getattr(self, col)}")

        return f"<{self.__class__.__name__} {', '.join(cols)}>"


class User(Base):
    """Таблица пользователей"""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id: Mapped[str] = mapped_column(index=True, unique=True)
    username: Mapped[str] = mapped_column(nullable=True)
    firstname: Mapped[str] = mapped_column(nullable=True)
    lastname: Mapped[str] = mapped_column(nullable=True)
    level: Mapped[Level] = mapped_column(String, index=True, nullable=True)
    gender: Mapped[str] = mapped_column(nullable=True)
    created_at: Mapped[datetime.datetime]
    updated_at: Mapped[datetime.datetime]
    is_banned: Mapped[bool] = mapped_column(default=False)
    is_admin: Mapped[bool] = mapped_column(default=False)

    events: Mapped[list["Event"]] = relationship(back_populates="users", secondary="events_users")

    def __str__(self):
        return f"{self.tg_id} {self.username + ' ' if self.username else ''}"


class Event(Base):
    """Таблица для событий"""
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[str]
    title: Mapped[str] = mapped_column(index=True)
    date: Mapped[datetime.datetime]
    places: Mapped[int]
    min_user_count: Mapped[int]
    active: Mapped[bool] = mapped_column(default=True)
    level: Mapped[int]
    price: Mapped[int]

    users: Mapped[list["User"]] = relationship(back_populates="events", secondary="events_users")

    def __str__(self):
        return f"{self.type} {self.title}"


class EventsUsers(Base):
    """Many-to-many relationship"""
    __tablename__ = "events_users"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), primary_key=True)