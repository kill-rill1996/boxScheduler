from aiogram import Router
from .start import router as start_router
from .registration import router as reg_router
from .profile import router as profile_router
from .menu import router as menu_router
from .events import router as events_router
from .add_events import router as add_events_router
from .admin import router as admin_router
from .edit_events import router as edit_events_router
from .my_events import router as my_events_router
from .players import router as player_router

main_router = Router()


main_router.include_routers(
    start_router,
    reg_router,
    profile_router,
    menu_router,
    add_events_router,
    events_router,
    admin_router,
    edit_events_router,
    my_events_router,
    player_router,
)