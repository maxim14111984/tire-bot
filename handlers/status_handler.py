# handlers/status_handler.py
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database.db import get_user_orders, update_order_status

router = Router()

@router.message(F.text == "/status")
async def show_orders_for_status(message: Message):
    orders = await get_user_orders(message.from_user.id)
    if not orders:
        await message.answer("У вас нет заказов.")
        return

    await message.answer("🔄 Выберите заказ для изменения статуса:")
    for order in orders:
        status = order.get("status", "В работе")
        # Кнопки только если статус "В работе"
        if status == "В работе":
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Готово", callback_data=f"status_{order['id']}_Готово"),
                    InlineKeyboardButton(text="🗑 Утиль", callback_data=f"status_{order['id']}_Утиль")
                ]
            ])
        else:
            kb = None  # Если уже "Готово" или "Утиль" — кнопок нет

        caption = (
            f"🔹 Номер: {order['tire_number']}\n"
            f"📝 Название: {order['name']}\n"
            f"📏 Размер: {order['size']}\n"
            f"👤 Клиент: {order['client']}\n"
            f"🔧 Работа: {order['work']}\n"
            f"🏷 Статус: {status}"
        )

        if order.get("file_id"):
            await message.answer_photo(photo=order["file_id"], caption=caption, reply_markup=kb)
        else:
            await message.answer(caption, reply_markup=kb)

@router.callback_query(F.data.startswith("status_"))
async def change_status(callback: CallbackQuery):
    try:
        _, order_id, new_status = callback.data.split("_")
        order_id = int(order_id)
        
        # Обновляем статус в БД
        await update_order_status(order_id, new_status)
        
        # Обновляем подпись под фото
        old_caption = callback.message.caption
        if old_caption:
            new_caption = "\n".join(
                line if not line.startswith("🏷 Статус:") else f"🏷 Статус: {new_status}"
                for line in old_caption.split("\n")
            )
            await callback.message.edit_caption(caption=new_caption)
        
        await callback.answer(f"✅ Статус изменён на: {new_status}")
    except Exception as e:
        await callback.answer("❌ Ошибка при изменении статуса", show_alert=True)
