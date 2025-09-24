from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from config import ADMIN_IDS

def get_start_kb(user_id: int):
    buttons = [
        [KeyboardButton(text="/start"), KeyboardButton(text="/orders")],
        [KeyboardButton(text="/find <номер>"), KeyboardButton(text="/export")]
    ]
    if user_id in ADMIN_IDS:
        buttons.append([KeyboardButton(text="/admin_orders")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
