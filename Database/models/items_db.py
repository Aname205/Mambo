class ItemsDB:
    def __init__(self, db):
        self.db = db

    async def create_table(self):
        async with self.db.cursor() as cursor:
            await cursor.execute("""CREATE TABLE IF NOT EXISTS items(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                emoji TEXT,
                item_type TEXT DEFAULT 'fish',
                is_locked INTEGER DEFAULT 0
            )""")
        await self.db.commit()

    async def get_item(self, item_id):
        async with self.db.cursor() as cursor:
            await cursor.execute(
                "SELECT * FROM items WHERE id = ?",
                (item_id,)
            )
            return await cursor.fetchone()

    async def get_item_by_name(self, item_name):
        async with self.db.cursor() as cursor:
            await cursor.execute("""
                SELECT i.id,
                    i.name,
                    i.emoji,
                    fi.price       AS fishing_price,
                    fi.description AS fishing_description,
                    mi.price       AS market_price,
                    mi.description AS market_description
                FROM items i
                    LEFT JOIN fishing_items fi ON i.id = fi.item_id
                    LEFT JOIN market_items mi ON i.id = mi.id
                WHERE LOWER(i.name) = LOWER(?)""", (item_name,)
            )
            return await cursor.fetchall()

    async def get_all_items(self):
        async with self.db.cursor() as cursor:
            await cursor.execute("SELECT * FROM items")
            return await cursor.fetchall()

    async def add_item(self, name, emoji, item_type='fish', is_locked=False):
        async with self.db.cursor() as cursor:
            await cursor.execute(
                "INSERT INTO items(name, emoji, item_type, is_locked) VALUES(?, ?, ?, ?)",
                (name, emoji, item_type, 1 if is_locked else 0)
            )
            rowid = cursor.lastrowid
        await self.db.commit()
        return rowid

    async def clear_all_items(self):
        async with self.db.cursor() as cursor:
            await cursor.execute("PRAGMA foreign_keys = OFF")

            await cursor.execute("DELETE FROM inventories")
            await cursor.execute("DELETE FROM fishing_items")
            await cursor.execute("DELETE FROM market_items")
            await cursor.execute("DELETE FROM items")

            await cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('items', 'inventories')")

            await cursor.execute("PRAGMA foreign_keys = ON")
        await self.db.commit()

    async def set_item_lock(self, item_id, is_locked):
        async with self.db.cursor() as cursor:
            await cursor.execute(
                "UPDATE items SET is_locked = ? WHERE id = ?",
                (1 if is_locked else 0, item_id)
            )
        await self.db.commit()
