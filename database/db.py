import aiosqlite
from datetime import datetime

DB_PATH = "tire_bot.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        # Таблица клиентов
        await db.execute("""
            CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT,
                is_corporate BOOLEAN DEFAULT 0
            )
        """)
        # Таблица шин
        await db.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                tire_number TEXT NOT NULL,
                file_id TEXT,
                name TEXT,          -- Название шины
                size TEXT,          -- Размер
                work TEXT,          -- Работа
                status TEXT DEFAULT 'В работе',
                created_at TEXT NOT NULL,
                FOREIGN KEY (client_id) REFERENCES clients (id) ON DELETE CASCADE
            )
        """)
        await db.commit()
    print("✅ База данных обновлена!")

# === КЛИЕНТЫ ===
async def get_or_create_client(name: str, phone: str = None):
    async with aiosqlite.connect(DB_PATH) as db:
        # Ищем клиента по имени и телефону
        cursor = await db.execute(
            "SELECT id, name, phone, is_corporate FROM clients WHERE name = ? OR phone = ?",
            (name, phone)
        )
        row = await cursor.fetchone()
        if row:
            return {"id": row[0], "name": row[1], "phone": row[2], "is_corporate": bool(row[3])}
        
        # Создаём нового клиента
        await db.execute(
            "INSERT INTO clients (name, phone) VALUES (?, ?)",
            (name, phone)
        )
        await db.commit()
        cursor = await db.execute("SELECT last_insert_rowid()")
        client_id = (await cursor.fetchone())[0]
        return {"id": client_id, "name": name, "phone": phone, "is_corporate": False}

async def search_clients(query: str):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            SELECT id, name, phone, is_corporate 
            FROM clients 
            WHERE name LIKE ? OR phone LIKE ?
            ORDER BY name
        """, (f"%{query}%", f"%{query}%"))
        rows = await cursor.fetchall()
        return [
            {"id": row[0], "name": row[1], "phone": row[2], "is_corporate": bool(row[3])}
            for row in rows
        ]

# === ЗАКАЗЫ (ШИНЫ) ===
async def save_order(client_id: int, tire_number: str, file_id: str = None,
                     name: str = None, size: str = None, work: str = None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO orders (client_id, tire_number, file_id, name, size, work, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (client_id, tire_number, file_id, name, size, work, datetime.now().isoformat()))
        await db.commit()

async def get_orders_by_client(client_id: int, status_filter: str = None):
    async with aiosqlite.connect(DB_PATH) as db:
        if status_filter:
            cursor = await db.execute("""
                SELECT id, tire_number, file_id, name, size, work, status, created_at
                FROM orders
                WHERE client_id = ? AND status = ?
                ORDER BY created_at DESC
            """, (client_id, status_filter))
        else:
            cursor = await db.execute("""
                SELECT id, tire_number, file_id, name, size, work, status, created_at
                FROM orders
                WHERE client_id = ?
                ORDER BY created_at DESC
            """, (client_id,))
        rows = await cursor.fetchall()
        return [{
            "id": row[0],
            "tire_number": row[1],
            "file_id": row[2],
            "name": row[3] or "",
            "size": row[4] or "",
            "work": row[5] or "",
            "status": row[6],
            "created_at": row[7]
        } for row in rows]

async def update_order_status(order_id: int, status: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
        await db.commit()

# === ЭКСПОРТ ===
async def export_client_orders_to_excel(client_id: int, filename: str) -> bool:
    try:
        import pandas as pd
        orders = await get_orders_by_client(client_id)
        if not orders:
            return False
        df = pd.DataFrame([
            {
                "Номер шины": o["tire_number"],
                "Название": o["name"],
                "Размер": o["size"],
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
