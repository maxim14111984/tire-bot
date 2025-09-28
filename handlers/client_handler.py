from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database.db import get_or_create_client, search_clients, get_orders_by_client, save_order, update_order_status
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

router = Router()

class ClientForm(StatesGroup):
    waiting_for_client = State()
    waiting_for_tire_number = State()
    waiting_for_name = State()
    waiting_for_size = State()
    waiting_for_work = State()

@router.message(F.photo)
async def handle_photo(message: Message, state: FSMContext):
    photo = message.photo[-1]
    file_id = photo.file_id
    tire_number = message.caption.strip() if message.caption else "не указано"
    await state.update_data(file_id=file_id, tire_number=tire_number)
    await message.answer("👤 Введите имя клиента или название компании:")
    await state.set_state(ClientForm.waiting_for_client)

@router.message(ClientForm.waiting_for_client)
async def process_client(message: Message, state: FSMContext):
    client_name = message.text.strip()
    client = await get_or_create_client(client_name)
    await state.update_data(client_id=client["id"], client_name=client["name"])
    await message.answer("✏️ Введите название шины (марку):")
    await state.set_state(ClientForm.waiting_for_name)

@router.message(ClientForm.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await message.answer("📏 Введите размер шины:")
    await state.set_state(ClientForm.waiting_for_size)

@router.message(ClientForm.waiting_for_size)
async def process_size(message: Message, state: FSMContext):
    await state.update_data(size=message.text.strip())
    await message.answer("🔧 Опишите работу:")
    await state.set_state(ClientForm.waiting_for_work)

@router.message(ClientForm.waiting_for_work)
async def process_work(message: Message, state: FSMContext):
    data = await state.get_data()
    data["work"] = message.text.strip()
    await save_order(
        client_id=data["client_id"],
        tire_number=data["tire_number"],
        file_id=data["file_id"],
        name=data["name"],
        size=data["size"],
        work=data["work"]
    )
    await message.answer(f"✅ Шина добавлена для клиента {data['client_name']}! Статус: В работе")
    await state.clear()

# === ПОИСК КЛИЕНТОВ ===
@router.message(F.text.startswith("/client "))
async def search_client_cmd(message: Message):
    query = message.text.replace("/client ", "").strip()
    if not query:
        await message.answer("🔍 Введите часть названия или телефона: /client СТГ")
        return
    clients = await search_clients(query)
    if not clients:
        await message.answer("Клиенты не найдены.")
        return
    for client in clients:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📁 Открыть папку", callback_data=f"client_{client['id']}")]
        ])
        contact = f"\n📞 {client['phone']}" if client['phone'] else ""
        await message.answer(f"{'🏢' if client['is_corporate'] else '👤'} {client['name']}{contact}", reply_markup=kb)

# === ПАПКА КЛИЕНТА ===
@router.callback_query(F.data.startswith("client_"))
async def open_client_folder(callback: CallbackQuery):
    client_id = int(callback.data.split("_")[1])
    # Показываем все шины клиента
    orders = await get_orders_by_client(client_id)
    if not orders:
        await callback.message.answer("У клиента нет шин.")
        return
    
    # Кнопки фильтрации
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="В работе", callback_data=f"filter_{client_id}_В работе"),
            InlineKeyboardButton(text="Готово", callback_data=f"filter_{client_id}_Готово")
        ],
        [
            InlineKeyboardButton(text="Утиль", callback_data=f"filter_{client_id}_Утиль"),
            InlineKeyboardButton(text="Все", callback_data=f"filter_{client_id}_Все")
        ]
    ])
    await callback.message.answer("Выберите статус:", reply_markup=kb)

@router.callback_query(F.data.startswith("filter_"))
async def filter_orders(callback: CallbackQuery):
    _, client_id, status = callback.data.split("_", 2)
    client_id = int(client_id)
    status_filter = None if status == "Все" else status
    orders = await get_orders_by_client(client_id, status_filter)
    if not orders:
        await callback.message.answer(f"Нет шин со статусом '{status}'.")
        return
    for order in orders:
        caption = f"🔹 {order['tire_number']}\n📝 {order['name']}\n📏 {order['size']}\n🔧 {order['work']}\n🏷 {order['status']}"
        if order["file_id"]:
            await callback.message.answer_photo(photo=order["file_id"], caption=caption)
        else:
            await callback.message.answer(caption)
