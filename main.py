import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message
from config import BOT_TOKEN, ADMIN_IDS
from database.db import init_db
from handlers.photo_handler import router as photo_router
from keyboards.reply_kb import get_start_kb

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(photo_router)

    @dp.message(lambda msg: msg.text == "/start")
    async def cmd_start(message: Message):
        user_id = message.from_user.id
        await message.answer(
            "👋 Добро пожаловать в бот учёта шин!\n\n"
            "📌 Команды:\n"
            "• /start — главное меню\n"
            "• /orders — мои заказы\n"
            "• /find <номер> — найти по номеру\n"
            "• /export — скачать Excel (мои заказы)\n"
            + ("• /admin_orders — все заказы (админ)\n" if user_id in ADMIN_IDS else ""),
            reply_markup=get_start_kb(user_id)
        )

    @dp.message(lambda msg: msg.text == "/orders")
    async def cmd_orders(message: Message):
        from database.db import get_user_orders
        orders = await get_user_orders(message.from_user.id)
        if not orders:
            await message.answer("У вас пока нет заказов.")
            return
        text = "📋 Ваши заказы:\n\n"
        for order in orders:
            text += f"🔹 {order['tire_number']} — {order['created_at']}\n"
        await message.answer(text)

    @dp.message(lambda msg: msg.text.startswith("/find "))
    async def cmd_find(message: Message):
        from database.db import find_order_by_number
        query = message.text.replace("/find ", "").strip()
        if not query:
            await message.answer("Пожалуйста, укажите номер шины: /find 12345")
            return
        orders = await find_order_by_number(query)
        if not orders:
            await message.answer("Не найдено заказов с таким номером.")
            return
        text = "🔍 Найденные заказы:\n\n"
        for order in orders:
            user_info = f"(админ)" if order['user_id'] in ADMIN_IDS else ""
            text += f"🔹 {order['tire_number']} — {order['created_at']} {user_info}\n"
        await message.answer(text)

    @dp.message(lambda msg: msg.text == "/export")
    async def cmd_export(message: Message):
        from database.db import export_user_orders_to_excel
        user_id = message.from_user.id
        filename = f"orders_{user_id}.xlsx"
        success = await export_user_orders_to_excel(user_id, filename)
        if not success:
            await message.answer("У вас нет заказов для экспорта.")
            return
        await message.answer_document(document=filename)
        import os
        os.remove(filename)

    @dp.message(lambda msg: msg.text == "/admin_orders")
    async def cmd_admin_orders(message: Message):
        if message.from_user.id not in ADMIN_IDS:
            await message.answer("❌ У вас нет доступа к этой команде.")
            return
        from database.db import get_all_orders
        orders = await get_all_orders()
        if not orders:
            await message.answer("Нет заказов в системе.")
            return
        text = "👑 Все заказы (админ):\n\n"
        for order in orders:
            text += f"🔹 {order['tire_number']} — @{order['user_id']} — {order['created_at']}\n"
        await message.answer(text)

    await init_db()

    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("🚀 Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
