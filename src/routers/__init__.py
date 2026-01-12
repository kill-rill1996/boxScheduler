from aiogram import Router
from .start import router as start_router
from .registration import router as reg_router
from .profile import router as profile_router
from .menu import router as menu_router
from .events import router as events_router

main_router = Router()


main_router.include_routers(
    start_router,
    reg_router,
    profile_router,
    menu_router,
    events_router,
)