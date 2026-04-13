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

    def get_tier_chances(self, modifier, monster_level=1, monster_base_level=1):
        """
        Calculate weighted tier chances.

        Tier ramp is driven by the *excess* levels above the monster's own base level:
            level_excess = max(0, monster_level - monster_base_level)

        At 0 excess  → baseline chances (no bonus).
        Every +2 levels above base → one tier step forward.
            level_factor = min(4.0, level_excess / 2.0)

        Examples:
            Slime  (base 1) at level 1 → level_factor 0.0 → baseline
            Slime  (base 1) at level 3 → level_factor 1.0 → uncommon bumped
            Bandit (base 5) at level 5 → level_factor 0.0 → baseline
            Bandit (base 5) at level 7 → level_factor 1.0 → uncommon bumped
        """

        TIER_DROP = {
            "common":    0.55,
            "uncommon":  0.20,
            "rare":      0.15,
            "epic":      0.07,
            "legendary": 0.03,
        }

        MODIFIER_TIER_BONUS = {
            "normal": {},
            "mystic":  {"uncommon": 1.4, "rare": 1.8, "epic": 1.8, "legendary": 1.5},
            "brutal":  {"uncommon": 0.9, "rare": 2.5, "epic": 2.0, "legendary": 1.8},
            "chaos":   {"uncommon": 0.8, "rare": 3.5, "epic": 2.5, "legendary": 2.0},
            "giant":   {"uncommon": 0.5, "rare": 8.0, "epic": 3.0, "legendary": 4.0},
        }

        chances = TIER_DROP.copy()

        # Apply modifier bonus
        for tier, mult in MODIFIER_TIER_BONUS.get(modifier, {}).items():
            chances[tier] *= mult

        # Apply level-excess bonus:
        # every 2 levels above base = 1 tier-factor step, capped at 4 steps (8 lvls above base)
        level_excess = max(0, monster_level - monster_base_level)
        level_factor = min(4.0, level_excess / 2.0)

        LEVEL_TIER_SCALING = {
            "uncommon":  0.5,   # fastest to ramp up
            "rare":      0.8,
            "epic":      1.1,
            "legendary": 1.4,
        }
        for tier, scale in LEVEL_TIER_SCALING.items():
            chances[tier] *= (1.0 + level_factor * scale)

        # Normalise so all chances sum to 1
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

    async def roll_loot(self, loot_table_id, modifier, monster_level=1, monster_base_level=1):

        items = await self.get_loot_items(loot_table_id)

        if not items:
            return []

        # get tier chances based on modifier + how far monster is above its base level
        tier_chances = self.get_tier_chances(modifier, monster_level, monster_base_level)

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

