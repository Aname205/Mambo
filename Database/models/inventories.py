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
            is_lock BOOLEAN,
            FOREIGN KEY (item_id) REFERENCES items(id)
        )
        """)
        await self.db.commit()

    async def get_inventory(self, user_id):
        async with self.db.cursor() as cursor:
            await cursor.execute("""
                SELECT i.id, i.name, i.emoji, fi.price, mi.price
                FROM inventories inv
                    JOIN items i ON inv.item_id = i.id
                    LEFT JOIN fishing_items fi ON i.id = fi.id
                    LEFT JOIN market_items mi ON i.id = mi.id
                WHERE inv.user_id = ? """, (user_id,)
            )
            return await cursor.fetchall()

    async def add_to_inventory(self, user_id, item_id):
        async with self.db.cursor() as cursor:
            await cursor.execute("""
                INSERT INTO inventories(user_id, item_id)
                VALUES(?,?) """, (user_id, item_id)
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
                WHERE user_id = ? """, (user_id,)
            )
            await self.db.commit()