class InventoriesDB:
    def __init__(self, db):
        self.db = db

    async def create_table(self):
        async with self.db.cursor() as cursor:
            await cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventories(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            item_id INTEGER,
            is_lock BOOLEAN DEFAULT 0,
            FOREIGN KEY (item_id) REFERENCES items(id)
        )
        """)
        await self.db.commit()

    async def get_inventory(self, user_id):
        async with self.db.cursor() as cursor:
            await cursor.execute("""
                SELECT inv.id, i.id, i.name, i.emoji, fi.tier, fi.price, mi.price, 
                        fi.description, mi.description, inv.is_lock
                FROM inventories inv
                    JOIN items i ON inv.item_id = i.id
                    LEFT JOIN fishing_items fi ON i.id = fi.item_id
                    LEFT JOIN market_items mi ON i.id = mi.id
                WHERE inv.user_id = ? """, (user_id,)
            )
            return await cursor.fetchall()

    async def add_to_inventory(self, user_id, item_id):
        async with self.db.cursor() as cursor:
            await cursor.execute("""
                INSERT INTO inventories(user_id, item_id, is_lock)
                VALUES(?,?,0) """, (user_id, item_id)
            )
            await self.db.commit()

    async def remove_from_inventory(self, user_id, item_id, amount):
        async with self.db.cursor() as cursor:
            await cursor.execute("""
                DELETE FROM inventories
                WHERE id IN (
                    SELECT id FROM inventories
                    WHERE user_id = ? AND item_id = ? LIMIT ?
                )""", (user_id, item_id, amount)
            )
            await self.db.commit()

    async def remove_all_from_inventory(self, user_id):
        async with self.db.cursor() as cursor:
            await cursor.execute(""" 
                DELETE FROM inventories 
                WHERE user_id = ? 
                AND is_lock = 0""", (user_id,)
            )
            await self.db.commit()

    async def set_item_lock(self, item_id, is_locked):
        async with self.db.cursor() as cursor:
            await cursor.execute(
                "UPDATE inventories SET is_lock = ? WHERE id = ?",
                (1 if is_locked else 0, item_id)
            )
        await self.db.commit()