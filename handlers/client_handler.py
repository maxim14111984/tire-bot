import os
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN, ADMIN_IDS
from database.db import init_db
from handlers.client_handler import router as client_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_bot():
    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    dp.include_router(client_router)

    @dp.message(lambda msg: msg.text and msg.text == "/start")
    async def cmd_start(message):
        await message.answer(
            "👋 Добро пожаловать!\n\n"
            "📌 Как пользоваться:\n"
            "1. Отправьте фото шины с подписью (номер)\n"
            "2. Следуйте инструкциям\n\n"
            "🔍 Поиск клиента: /client <название или телефон>"
        )

    await init_db()
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("🚀 Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(run_bot())
