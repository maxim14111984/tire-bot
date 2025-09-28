from aiogram import Router, F
from aiogram.types import Message
from database.db import save_order

# Создаём роутер — именно он нужен для импорта в main.py
router = Router()

@router.message(F.photo)
async def handle_photo(message: Message):
    user_id = message.from_user.id
    photo = message.photo[-1]  # Берём фото в максимальном разрешении
    file_id = photo.file_id

    # Получаем номер шины из подписи к фото
    tire_number = message.caption.strip() if message.caption else "не указано"

    # Сохраняем заказ в базу данных
    await save_order(user_id, tire_number, file_id)

    # Отправляем подтверждение
    await message.answer(f"✅ Шина '{tire_number}' добавлена в учёт!")
