# handlers/form_handler.py
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database.db import save_order

router = Router()

class TireForm(StatesGroup):
    waiting_for_name = State()
    waiting_for_size = State()
    waiting_for_client = State()
    waiting_for_work = State()

@router.message(F.photo)
async def handle_photo(message: Message, state: FSMContext):
    # Сохраняем данные фото и номер шины (из подписи)
    photo = message.photo[-1]
    file_id = photo.file_id
    tire_number = message.caption.strip() if message.caption else "не указано"
    
    # Сохраняем во временное хранилище (FSM)
    await state.update_data(
        file_id=file_id,
        tire_number=tire_number,
        user_id=message.from_user.id
    )
    
    # Запрашиваем название
    await message.answer("✏️ Введите название шины (марку):")
    await state.set_state(TireForm.waiting_for_name)

@router.message(TireForm.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await message.answer("📏 Введите размер шины (например, 205/55 R16):")
    await state.set_state(TireForm.waiting_for_size)

@router.message(TireForm.waiting_for_size)
async def process_size(message: Message, state: FSMContext):
    await state.update_data(size=message.text.strip())
    await message.answer("👤 Введите данные клиента (имя или телефон):")
    await state.set_state(TireForm.waiting_for_client)

@router.message(TireForm.waiting_for_client)
async def process_client(message: Message, state: FSMContext):
    await state.update_data(client=message.text.strip())
    await message.answer("🔧 Опишите работу (ремонт, балансировка, замена и т.д.):")
    await state.set_state(TireForm.waiting_for_work)

@router.message(TireForm.waiting_for_work)
async def process_work(message: Message, state: FSMContext):
    # Получаем все данные
    data = await state.get_data()
    data["work"] = message.text.strip()
    
    # Сохраняем в базу данных
    await save_order(
        user_id=data["user_id"],
        tire_number=data["tire_number"],
        file_id=data["file_id"],
        name=data["name"],
        size=data["size"],
        client=data["client"],
        work=data["work"]
    )
    
    await message.answer("✅ Заказ создан! Статус: **В работе**", parse_mode="Markdown")
    await state.clear()  # Очищаем состояние
