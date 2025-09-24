import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(","))) if os.getenv("ADMIN_IDS") else []

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN не задан в переменных окружения!")
