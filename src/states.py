from aiogram.fsm.state import StatesGroup, State


class Registration(StatesGroup):
    name = State()
    gender = State()


class UpdateUser(StatesGroup):
    name = State()