# main.py
import os
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN, ADMIN_IDS
from database.db import init_db
from handlers.photo_handler import router as photo_router
from keyboards.reply_kb import get_start_kb

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_bot():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(photo_router)

    @dp.message(lambda msg: msg.text and msg.text == "/start")
    async def cmd_start(message):
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

    @dp.message(lambda msg: msg.text and msg.text == "/orders")
    async def cmd_orders(message):
        from database.db import get_user_orders
        orders = await get_user_orders(message.from_user.id)
        if not orders:
            await message.answer("У вас пока нет заказов.")
            return
        
        await message.answer("📋 Ваши заказы:")
        for order in orders:
            if order.get("file_id"):
                await message.answer_photo(
                    photo=order["file_id"],
                    caption=f"🔹 Номер шины: {order['tire_number']}\n📅 Дата: {order['created_at']}"
                )
            else:
                await message.answer(f"🔹 {order['tire_number']} — {order['created_at']}")

    @dp.message(lambda msg: msg.text and msg.text.startswith("/find "))
    async def cmd_find(message):
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
            user_info = " (админ)" if order['user_id'] in ADMIN_IDS else ""
            text += f"🔹 {order['tire_number']} — {order['created_at']}{user_info}\n"
        await message.answer(text)

    @dp.message(lambda msg: msg.text and msg.text == "/export")
    async def cmd_export(message):
        from database.db import export_user_orders_to_excel
        user_id = message.from_user.id
        filename = f"orders_{user_id}.xlsx"
        if await export_user_orders_to_excel(user_id, filename):
            await message.answer_document(document=filename)
            os.remove(filename)
        else:
            await message.answer("У вас нет заказов для экспорта.")

    @dp.message(lambda msg: msg.text and msg.text == "/admin_orders")
    async def cmd_admin_orders(message):
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
    # Запуск бота
    asyncio.run(run_bot())
