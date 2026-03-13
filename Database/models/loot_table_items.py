import random

class LootTableItemsDB:
    def __init__(self, db):
        self.db = db

    async def create_table(self):
        async with self.db.cursor() as cursor:
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS loot_table_items(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    loot_table_id INTEGER,
                    item_id INTEGER,
                    drop_chance REAL,
                    min_amount INTEGER DEFAULT 1,
                    max_amount INTEGER DEFAULT 1,
                    
                    UNIQUE(loot_table_id, item_id),

                    FOREIGN KEY (loot_table_id) REFERENCES loot_tables(id),
                    FOREIGN KEY (item_id) REFERENCES items(id)
                )
            """)
        await self.db.commit()

    async def add_loot_item(
            self,
            loot_table_id,
            item_id,
            drop_chance,
            min_amount=1,
            max_amount=1
    ):
        async with self.db.cursor() as cursor:
            await cursor.execute("""
                INSERT INTO loot_table_items(
                    loot_table_id,
                    item_id,
                    drop_chance,
                    min_amount,
                    max_amount)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(loot_table_id, item_id)
                DO UPDATE SET
                    drop_chance = excluded.drop_chance,
                    min_amount = excluded.min_amount,
                    max_amount = excluded.max_amount
             """, (
                 loot_table_id,
                 item_id,
                 drop_chance,
                 min_amount,
                 max_amount
             ))
        await self.db.commit()

    async def get_loot_items(self, loot_table_id):
        async with self.db.cursor() as cursor:
            await cursor.execute("""
                SELECT
                    lti.item_id,
                    lti.drop_chance,
                    lti.min_amount,
                    lti.max_amount,
                    i.name,
                    i.emoji,
                    i.item_type,
                    COALESCE(fi.tier, mi.tier, em.tier) AS item_tier
                FROM loot_table_items lti
                    JOIN items i ON lti.item_id = i.id
                    LEFT JOIN fishing_items fi ON i.id = fi.item_id
                    LEFT JOIN market_items mi ON i.id = mi.id
                    LEFT JOIN equipments em ON i.id = em.item_id
                WHERE lti.loot_table_id = ?
                """, (loot_table_id,))

            return await cursor.fetchall()

    def get_tier_chances(self, modifier):

        TIER_DROP = {
            "common": 0.67,
            "uncommon": 0.18,
            "rare": 0.1,
            "epic": 0.04,
            "legendary": 0.01
        }

        MODIFIER_TIER_BONUS = {

            "normal": {},

            "mystic": {
                "uncommon": 1.2,
                "rare": 1.4,
                "epic": 1.6,
                "legendary": 2
            },

            "brutal": {
                "uncommon": 1.2,
                "rare": 1.4,
                "epic": 1.6,
                "legendary": 2
            },

            "chaos": {
                "uncommon": 1.2,
                "rare": 1.4,
                "epic": 1.6,
                "legendary": 2
            },

            "giant": {
                "uncommon": 1.2,
                "rare": 1.4,
                "epic": 1.6,
                "legendary": 2
            }
        }

        chances = TIER_DROP.copy()

        bonus = MODIFIER_TIER_BONUS.get(modifier, {})

        for tier, mult in bonus.items():
            chances[tier] *= mult

        total = sum(chances.values())

        for t in chances:
            chances[t] /= total

        return chances

    def roll_tier(self, chances):
        r = random.random()
        cumulative = 0

        for tier, chance in chances.items():
            cumulative += chance
            if r <= cumulative:
                return tier

        return "common"

    async def roll_loot(self, loot_table_id, modifier):

        items = await self.get_loot_items(loot_table_id)

        if not items:
            return []

        # get tier chances based on modifier
        tier_chances = self.get_tier_chances(modifier)

        drops = []

        roll_count = random.randint(1, 3)

        for _ in range(roll_count):

            rolled_tier = self.roll_tier(tier_chances)

            tier_items = [i for i in items if i[7] == rolled_tier]

            if not tier_items:
                continue

            item = random.choice(tier_items)

            item_id, chance, min_amt, max_amt, name, emoji, item_type, tier = item

            if random.random() <= chance:
                amount = random.randint(min_amt, max_amt)

                drops.append({
                    "item_id": item_id,
                    "name": name,
                    "emoji": emoji,
                    "amount": amount,
                    "tier": tier
                })

        return drops

