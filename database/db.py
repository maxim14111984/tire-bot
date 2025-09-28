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
            "SELECT id, user_id, tire_number, created_at, file_id, name, size, client, work, status FROM orders ORDER BY created_at DESC"
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

async def save_order(user_id: int, tire_number: str, file_id: str = None,
                     name: str = None, size: str = None,
                     client: str = None, work: str = None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO orders (user_id, tire_number, file_id, name, size, client, work, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, tire_number, file_id, name, size, client, work, datetime.now().isoformat()))
        await db.commit()

async def update_order_status(order_id: int, status: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
        await db.commit()

async def export_user_orders_to_excel(user_id: int, filename: str) -> bool:
    try:
        import pandas as pd
        orders = await get_user_orders(user_id)
        if not orders:
            return False
        df = pd.DataFrame([
            {
                "Номер шины": o["tire_number"],
                "Название": o["name"],
                "Размер": o["size"],
                "Клиент": o["client"],
                "Работа": o["work"],
                "Статус": o["status"],
                "Дата": o["created_at"]
            }
            for o in orders
        ])
        df.to_excel(filename, index=False)
        return True
    except Exception as e:
        print(f"Ошибка экспорта: {e}")
        return False
