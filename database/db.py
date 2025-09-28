import aiosqlite
from datetime import datetime

DB_PATH = "tire_bot.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                tire_number TEXT NOT NULL,
                file_id TEXT,
                created_at TEXT NOT NULL
            )
        """)
        # Попытка добавить колонку file_id, если таблица уже существовала без неё
        try:
            await db.execute("ALTER TABLE orders ADD COLUMN file_id TEXT")
        except aiosqlite.OperationalError:
            # Колонка уже существует — ничего не делаем
            pass
        await db.commit()
    print("✅ База данных инициализирована!")

async def get_user_orders(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT tire_number, created_at, file_id FROM orders WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,)
        )
        rows = await cursor.fetchall()
        return [{"tire_number": row[0], "created_at": row[1], "file_id": row[2]} for row in rows]

async def find_order_by_number(query: str):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT user_id, tire_number, created_at, file_id FROM orders WHERE tire_number LIKE ? ORDER BY created_at DESC",
            (f"%{query}%",)
        )
        rows = await cursor.fetchall()
        return [{"user_id": row[0], "tire_number": row[1], "created_at": row[2], "file_id": row[3]} for row in rows]

async def get_all_orders():
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT user_id, tire_number, created_at, file_id FROM orders ORDER BY created_at DESC"
        )
        rows = await cursor.fetchall()
        return [{"user_id": row[0], "tire_number": row[1], "created_at": row[2], "file_id": row[3]} for row in rows]

async def save_order(user_id: int, tire_number: str, file_id: str = None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO orders (user_id, tire_number, file_id, created_at) VALUES (?, ?, ?, ?)",
            (user_id, tire_number, file_id, datetime.now().isoformat())
        )
        await db.commit()

async def export_user_orders_to_excel(user_id: int, filename: str) -> bool:
    try:
        import pandas as pd
        orders = await get_user_orders(user_id)
        if not orders:
            return False
        df = pd.DataFrame([
            {"tire_number": o["tire_number"], "created_at": o["created_at"]}
            for o in orders
        ])
        df.to_excel(filename, index=False)
        return True
    except Exception as e:
        print(f"Ошибка экспорта: {e}")
        return False
