import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode

from config import settings
from handlers.start_handler import router as start_router
from handlers.navigation_menu_handlers import router as nav_router
from database.connection import close_pool
from middlewares.logging_middleware import InteractionLoggingMiddleware

async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="\n%(asctime)s | %(levelname)s | %(message)s",
    )
    # подавим подробные логи aiogram
    for noisy in ("aiogram.event", "aiogram.dispatcher"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
    bot = Bot(token=settings.bot_token, parse_mode=ParseMode.HTML)
    dp = Dispatcher()
    # Middlewares
    dp.message.middleware(InteractionLoggingMiddleware())
    dp.callback_query.middleware(InteractionLoggingMiddleware())

    dp.include_router(start_router)
    dp.include_router(nav_router)
    try:
        await dp.start_polling(bot)
    finally:
        await close_pool()

if __name__ == "__main__":
    asyncio.run(main()) 