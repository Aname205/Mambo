class FishingItemsDB:
    def __init__(self, db):
        self.db = db

    async def create_table(self):
        async with self.db.cursor() as cursor:
            await cursor.execute("""
        CREATE TABLE IF NOT EXISTS fishing_items(
            id INTEGER PRIMARY KEY,
            price INTEGER,
            tier TEXT,
            fishing_rate REAL,
            description TEXT,
            FOREIGN KEY (id) REFERENCES items(id)
        )
        """)
        await self.db.commit()

    async def get_fishing_items(self):
        async with self.db.cursor() as cursor:
            await cursor.execute("""
                SELECT i.id, i.name, i.emoji, fi.fishing_rate
                FROM items i
                INNER JOIN fishing_items fi ON i.id = fi.id
            """)
            return await cursor.fetchall()

    async def add_fishing_item(self, item_id, price, tier, fishing_rate, description=None):
        async with self.db.cursor() as cursor:
            await cursor.execute("""
                INSERT INTO fishing_items(id, price, tier, fishing_rate, description)
                VALUES(?, ?, ?, ?, ?)
                """, (item_id, price, tier, fishing_rate, description or ""))
            await self.db.commit()