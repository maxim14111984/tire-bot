# main.py
import os
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN, ADMIN_IDS
from database.db import init_db
from handlers.form_handler import router as form_router
from handlers.status_handler import router as status_router
from keyboards.reply_kb import get_start_kb

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_bot():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(form_router)
    dp.include_router(status_router)

    @dp.message(lambda msg: msg.text and msg.text == "/start")
    async def cmd_start(message):
        user_id = message.from_user.id
        await message.answer(
            "👋 Добро пожаловать в бот учёта шин!\n\n"
            "📌 Команды:\n"
            "• /start — главное меню\n"
            "• /orders — мои заказы\n"
            "• /status — изменить статус заказа\n"
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
            caption = (
                f"🔹 Номер шины: {order['tire_number']}\n"
                f"📝 Название: {order['name']}\n"
                f"📏 Размер: {order['size']}\n"
                f"👤 Клиент: {order['client']}\n"
                f"🔧 Работа: {order['work']}\n"
                f"🏷 Статус: {order['status']}\n"
                f"📅 Дата: {order['created_at']}"
            )
            if order.get("file_id"):
                await message.answer_photo(photo=order["file_id"], caption=caption)
            else:
                await message.answer(caption)

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
        await message.answer("🔍 Найденные заказы:")
        for order in orders:
            caption = (
                f"🔹 Номер: {order['tire_number']}\n"
                f"📝 Название: {order['name']}\n"
                f"📏 Размер: {order['size']}\n"
                f"👤 Клиент: {order['client']}\n"
                f"🔧 Работа: {order['work']}\n"
                f"🏷 Статус: {order['status']}\n"
                f"📅 Дата: {order['created_at']}"
            )
            if order.get("file_id"):
                await message.answer_photo(photo=order["file_id"], caption=caption)
            else:
                await
