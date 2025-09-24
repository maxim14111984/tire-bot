from aiogram import Router, F
from aiogram.types import Message
from database.db import save_order

router = Router()

@router.message(F.photo)
async def handle_photo(message: Message):
    user_id = message.from_user.id
    photo = message.photo[-1]
    file_id = photo.file_id

    tire_number = message.caption.strip() if message.caption else "не указано"

    await save_order(user_id, tire_number, file_id)

    await message.answer(f"✅ Шина '{tire_number}' добавлена в учёт!")
