import asyncpg
import os
from datetime import datetime

DATABASE_URL = os.getenv("DATABASE_URL")

async def init_db():
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            tire_number TEXT NOT NULL,
            photo_path TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    await conn.close()
    print("✅ База данных инициализирована")

async def get_user_orders(user_id: int):
    conn = await asyncpg.connect(DATABASE_URL)
    rows = await conn.fetch("SELECT tire_number, created_at FROM orders WHERE user_id = $1 ORDER BY created_at DESC", user_id)
    await conn.close()
    return [{"tire_number": row["tire_number"], "created_at": row["created_at"]} for row in rows]

async def find_order_by_number(tire_number: str):
    conn = await asyncpg.connect(DATABASE_URL)
    rows = await conn.fetch(
        "SELECT user_id, tire_number, created_at FROM orders WHERE tire_number ILIKE $1 ORDER BY created_at DESC",
        f"%{tire_number}%"
    )
    await conn.close()
    return [{"user_id": row["user_id"], "tire_number": row["tire_number"], "created_at": row["created_at"]} for row in rows]

async def get_all_orders():
    conn = await asyncpg.connect(DATABASE_URL)
    rows = await conn.fetch("SELECT user_id, tire_number, created_at FROM orders ORDER BY created_at DESC")
    await conn.close()
    return [{"user_id": row["user_id"], "tire_number": row["tire_number"], "created_at": row["created_at"]} for row in rows]

async def export_user_orders_to_excel(user_id: int, filename: str):
    import pandas as pd
    orders = await get_user_orders(user_id)
    if not orders:
        return False
    df = pd.DataFrame(orders)
    df.to_excel(filename, index=False, sheet_name="Заказы")
    return True

async def save_order(user_id: int, tire_number: str, photo_path: str):
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute(
        "INSERT INTO orders (user_id, tire_number, photo_path) VALUES ($1, $2, $3)",
        user_id, tire_number, photo_path
    )
    await conn.close()
