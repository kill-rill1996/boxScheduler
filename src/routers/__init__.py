from aiogram import Router
from .start import router as start_router
from .registration import router as reg_router

main_router = Router()


main_router.include_routers(
    start_router,
    reg_router,
)