import aiosqlite
from datetime import datetime

DB_PATH = "tire_bot.db"

# ... весь ваш код ...

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
  # ← Вот здесь должна быть пустая строка (нажмите Enter в конце файла)
