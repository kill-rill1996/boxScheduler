from aiogram.fsm.state import StatesGroup, State


class Registration(StatesGroup):
    name = State()
    gender = State()


class UpdateUser(StatesGroup):
    name = State()


class AddEventFSM(StatesGroup):
    type = State()
    title = State()
    date = State()
    time = State()
    places = State()
    min_count = State()
    price = State()