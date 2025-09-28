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
                name TEXT,
                size TEXT,
                client TEXT,
                work TEXT,
                status TEXT DEFAULT 'В работе',
                created_at TEXT NOT NULL
            )
        """)
        # Добавляем новые колонки, если они ещё не существуют
        new_columns = ["name", "size", "client", "work", "status"]
        for col in new_columns:
            try:
                await db.execute(f"ALTER TABLE orders ADD COLUMN {col} TEXT")
            except aiosqlite.OperationalError:
                pass  # Колонка уже существует
        await db.commit()
    print("✅ База данных обновлена!")

async def get_user_orders(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id, tire_number, created_at, file_id, name, size, client, work, status FROM orders WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,)
        )
        rows = await cursor.fetchall()
        return [{
            "id": row[0],
            "tire_number": row[1],
            "created_at": row[2],
            "file_id": row[3],
            "name": row[4] or "",
            "size": row[5] or "",
            "client": row[6] or "",
            "work": row[7] or "",
            "status": row[8] or "В работе"
        } for row in rows]

async def find_order_by_number(query: str):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id, user_id, tire_number, created_at, file_id, name, size, client, work, status FROM orders WHERE tire_number LIKE ? ORDER BY created_at DESC",
            (f"%{query}%",)
        )
        rows = await cursor.fetchall()
        return [{
            "id": row[0],
            "user_id": row[1],
            "tire_number": row[2],
            "created_at": row[3],
            "file_id": row[4],
            "name": row[5] or "",
            "size": row[6] or "",
            "client": row[7] or "",
            "work": row[8] or "",
            "status": row[9] or "В работе"
        } for row in rows]

async def get_all_orders():
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id, user_id, tire_number, created_at, file_id, name, size,
