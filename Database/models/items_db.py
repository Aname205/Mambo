class ItemsDB:
    def __init__(self, db):
        self.db = db

    async def create_table(self):
        async with self.db.cursor() as cursor:
            await cursor.execute("""CREATE TABLE IF NOT EXISTS items(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                emoji TEXT,
                item_type TEXT
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
                    i.item_type,
                    fi.price       AS fishing_price,
                    fi.description AS fishing_description,
                    mi.price       AS market_price,
                    mi.description AS market_description,
                    COALESCE(fi.tier, mi.tier, em.tier) AS item_tier,
                    em.damage,
                    em.armor,
                    em.break_force,
                    em.price,
                    em.critical_chance,
                    em.dodge_chance
                FROM items i
                    LEFT JOIN fishing_items fi ON i.id = fi.item_id
                    LEFT JOIN market_items mi ON i.id = mi.id
                    LEFT JOIN equipments em ON i.id = em.item_id
                WHERE LOWER(i.name) LIKE LOWER(?)
                ORDER BY
                CASE item_tier
                    WHEN 'common' THEN 1
                    WHEN 'uncommon' THEN 2
                    WHEN 'rare' THEN 3
                    WHEN 'epic' THEN 4
                    WHEN 'legendary' THEN 5
                END
            """, (item_name,)
            )
            return await cursor.fetchall()

    async def get_all_items(self):
        async with self.db.cursor() as cursor:
            await cursor.execute("SELECT * FROM items")
            return await cursor.fetchall()

    async def get_or_create_item(self, name, emoji, item_type):
        async with self.db.cursor() as cursor:
            await cursor.execute("""
                SELECT id FROM items
                WHERE name = ? AND item_type = ?
            """, (name, item_type))

            row = await cursor.fetchone()

            if row:
                return row[0]

            await cursor.execute("""
                INSERT INTO items(name, emoji, item_type)
                VALUES (?, ?, ?)
            """, (name, emoji, item_type))

            await self.db.commit()
            return cursor.lastrowid

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

