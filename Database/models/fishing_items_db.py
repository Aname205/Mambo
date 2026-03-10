class FishingItemsDB:
    def __init__(self, db):
        self.db = db

    async def create_table(self):
        async with self.db.cursor() as cursor:
            await cursor.execute("""
        CREATE TABLE IF NOT EXISTS fishing_items(
            id INTEGER PRIMARY KEY,
            item_id INTEGER,
            price INTEGER,
            tier TEXT,
            fishing_rate REAL,
            description TEXT,
            FOREIGN KEY (item_id) REFERENCES items(id)
        )
        """)
        await self.db.commit()

    async def get_fishing_items(self):
        async with self.db.cursor() as cursor:
            await cursor.execute("""
                SELECT i.id, i.name, i.emoji,fi.tier , fi.fishing_rate
                FROM items i
                INNER JOIN fishing_items fi ON i.id = fi.item_id
            """)
            return await cursor.fetchall()

    async def add_fishing_item(self, item_id, price, tier, fishing_rate, description=None):
        async with self.db.cursor() as cursor:
            await cursor.execute("""
                INSERT INTO fishing_items(item_id, price, tier, fishing_rate, description)
                VALUES(?, ?, ?, ?, ?)
                """, (item_id, price, tier, fishing_rate, description or ""))
            await self.db.commit()

    # Fish pool generation
    async def generate_default_pool(self, items_db):
        pool = [
            ("Minnow", "🐟", 25, "common", 150, "A tiny fish"),
            ("Minnow", "🐟", 35, "uncommon", 100, "A tiny fish"),
            ("Minnow", "🐟", 40, "rare", 75, "A tiny fish"),
            ("Minnow", "🐟", 50, "epic", 50, "A tiny fish"),
            ("Minnow", "🐟", 60, "legendary", 25, "A tiny fish"),
            ("Bass", "🐠", 80, "common", 125, "A decent catch"),
            ("Bass", "🐠", 90, "uncommon", 90, "A decent catch"),
            ("Bass", "🐠", 100, "rare", 65, "A decent catch"),
            ("Bass", "🐠", 120, "epic", 50, "A decent catch"),
            ("Bass", "🐠", 150, "legendary", 20, "A decent catch"),
            ("Octopus", "🐙", 200, "uncommon", 60, "Squishy"),
            ("Octopus", "🐙", 250, "rare", 45, "Squishy"),
            ("Octopus", "🐙", 350, "epic", 30, "Squishy"),
            ("Octopus", "🐙", 500, "legendary", 15, "Squishy"),
            ("Shark", "🦈", 400, "rare", 35, "Fierce predator"),
            ("Shark", "🦈", 600, "epic", 25, "Fierce predator"),
            ("Shark", "🦈", 900, "legendary", 10, "Fierce predator"),
            ("Kraken", "🦑", 2000, "epic", 25, "Nightmare for those who sails"),
            ("Kraken", "🦑", 4500, "legendary", 5, "Nightmare for those who sails"),
        ]

        for name, emoji, price, tier, fishing_rate, description in pool:
            item_id = await items_db.add_item(name, emoji, "fish")
            await self.add_fishing_item(item_id, price, tier, fishing_rate, description)

    async def ensure_pool(self, items_db):
        async with self.db.cursor() as cursor:
            await cursor.execute("SELECT COUNT(*) FROM fishing_items")
            count = (await cursor.fetchone())[0]

        if count == 0:
            await self.generate_default_pool(items_db)