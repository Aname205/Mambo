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
            tier TEXT DEFAULT 'common' CHECK(tier in ('common', 'uncommon', 'rare', 'epic', 'legendary')),
            fishing_rate REAL,
            description TEXT,
            UNIQUE(item_id, tier),
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
                INSERT OR REPLACE INTO fishing_items(item_id, price, tier, fishing_rate, description)
                VALUES(?, ?, ?, ?, ?)
                """, (item_id, price, tier, fishing_rate, description or ""))

    # Fish pool generation


    async def generate_default_pool(self, items_db):
        base_fish = [
            ("Minnow", "🐟", 25, 500, "A tiny fish"),
            ("Bass", "🐠", 80, 250, "A decent catch"),
            ("Octopus", "🐙", 200, 150, "Squishy"),
            ("Shark", "🦈", 400, 75, "Fierce predator"),
            ("Kraken", "🦑", 2000, 25, "Nightmare for sailors"),
        ]

        TIERS = {
            "common": {
                "price_mult": 1.0,
                "rate_mult": 1.0
            },
            "uncommon": {
                "price_mult": 1.4,
                "rate_mult": 0.7
            },
            "rare": {
                "price_mult": 1.8,
                "rate_mult": 0.5
            },
            "epic": {
                "price_mult": 2.5,
                "rate_mult": 0.3
            },
            "legendary": {
                "price_mult": 4.0,
                "rate_mult": 0.15
            }
        }

        valid_keys = []

        for name, emoji, base_price, base_rate, desc in base_fish:

            item_id = await items_db.get_or_create_item(name, emoji, "fish")

            for tier, mult in TIERS.items():
                price = int(base_price * mult["price_mult"])
                rate = base_rate * mult["rate_mult"]

                await self.add_fishing_item(item_id, price, tier, rate, desc)

                valid_keys.append((item_id, tier))

        # Remove rows not in pool anymore
        async with self.db.cursor() as cursor:

            if valid_keys:
                placeholders = ",".join(["(?, ?)"] * len(valid_keys))

                values = [v for pair in valid_keys for v in pair]

                await cursor.execute(f"""
                    DELETE FROM fishing_items
                    WHERE (item_id, tier) NOT IN ({placeholders})
                """, values)

        await self.db.commit()

        # Remove fish not in base pool
        valid_names = [fish[0] for fish in base_fish]

        async with self.db.cursor() as cursor:

            placeholders = ",".join("?" * len(valid_names))

            await cursor.execute(f"""
                DELETE FROM items
                WHERE item_type='fish'
                AND name NOT IN ({placeholders})
            """, valid_names)

        await self.db.commit()

    async def ensure_pool(self, items_db):
        await self.generate_default_pool(items_db)