class EquipmentsDB:
    def __init__(self, db):
        self.db = db

    async def create_table(self):
        async with self.db.cursor() as cursor:
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS equipments(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_id INTEGER,
                    equipment_type TEXT NOT NULL CHECK(equipment_type IN ('weapon', 'armor', 'accessory')),
                    health INTEGER DEFAULT 0,
                    damage INTEGER DEFAULT 0,
                    armor INTEGER DEFAULT 0,
                    speed INTEGER DEFAULT 0,
                    break_force INTEGER DEFAULT 0,
                    tier TEXT DEFAULT 'common' CHECK(tier IN ('common','uncommon','rare','epic','legendary')),
                    price INTEGER DEFAULT 0,
                    critical_chance REAL DEFAULT 0,
                    dodge_chance REAL DEFAULT 0,
                    market_only BOOLEAN DEFAULT 0,
                    UNIQUE(item_id, tier),
                    FOREIGN KEY (item_id) REFERENCES items(id)
                )
            """)
        await self.db.commit()

    async def add_equipment(
            self,
            item_id,
            equipment_type,
            health=0,
            damage=0,
            armor=0,
            speed=0,
            break_force=0,
            tier="common",
            price=0,
            critical_chance=0,
            dodge_chance=0,
            market_only=False
    ):
        async with self.db.cursor() as cursor:
            await cursor.execute("""
                INSERT INTO equipments(
                    item_id, 
                    equipment_type, 
                    health,
                    damage, 
                    armor,
                    speed,
                    break_force, 
                    tier, 
                    price, 
                    critical_chance, 
                    dodge_chance,
                    market_only
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (item_id, tier)
                DO UPDATE SET
                    equipment_type = excluded.equipment_type,
                    health = excluded.health,
                    damage = excluded.damage,
                    armor = excluded.armor,
                    speed = excluded.speed,
                    break_force = excluded.break_force,
                    price = excluded.price,
                    critical_chance = excluded.critical_chance,
                    dodge_chance = excluded.dodge_chance,
                    market_only = excluded.market_only
                """,(
                        item_id,
                        equipment_type,
                        health,
                        damage,
                        armor,
                        speed,
                        break_force,
                        tier,
                        price,
                        critical_chance,
                        dodge_chance,
                        1 if market_only else 0
                    )
                )
        await self.db.commit()

    async def get_equipment(self, item_id):
        async with self.db.cursor() as cursor:
            await cursor.execute("""
                    SELECT * FROM equipments
                    INNER JOIN items ON items.id = equipments.item_id
                    WHERE equipments.item_id = ?""", (item_id,))

            equipment = await cursor.fetchall()

        return equipment

    async def get_equipment_by_type(self, equipment_type):
        async with self.db.cursor() as cursor:
            await cursor.execute("""
                SELECT * FROM equipments
                INNER JOIN items ON items.id = equipments.item_id
                WHERE equipment_type = ?
                """, (equipment_type,))

            items = await cursor.fetchall()

        return items

    async def get_equipment_by_tier(self, tier):
        async with self.db.cursor() as cursor:
            await cursor.execute("""
                SELECT * FROM equipments
                INNER JOIN items ON items.id = equipments.item_id
                WHERE tier = ?
                """, (tier,))

            items = await cursor.fetchall()

        return items

    async def generate_equipments(self, items_db):
        try:
            market_equipments = [
                ("Wooden Sword", "🗡️", "weapon", 0, 6, 0, 2, 2, 1000, 0.02, 0.01),
                ("Steel Dagger", "🔪", "weapon", 0, 14, 0, 5, 1, 3000, 0.07, 0.05),
                ("Knight Longsword", "⚔️", "weapon", 0, 25, 0, -4, 6, 9000, 0.1, 0),
                ("Wooden Armor", "🛡", "armor", 20, 0, 3, 0, 0, 1500, 0, 0),
                ("Hunter Jacket", "🥋", "armor", 40, 0, 6, 2, 0, 4500, 0, 0.03),
                ("Steel Armor", "🛡️", "armor", 80, 0, 14, -4, 0, 10000, 0, 0),
                ("Crude Speed Gem", "💎", "accessory", 0, 0, 0, 3, 0, 1000, 0, 0),
                ("Crude Blood Gem", "🔴", "accessory", 10, 0, 0, 0, 0, 1000, 0, 0),
            ]

            base_equipments = [
                # Fields: name, emoji, equipment_type,      hp,   dmg,  armor, speed, break, price, crit, dodge
                ("Rusty Copper Sword", "🗡️", "weapon",      0,    7,    0,     2,     3,     30,    0.02, 0.01),
                ("Rusty Copper Armor", "🛡", "armor",       30,    0,    4,     0,     0,     30,    0,    0),
                ("Rusty Copper Axe" , "🪓", "weapon",       0,    11,   0,     -1,    5,     30,    0.02, 0),
                ("Rusty Copper Knife" , "🔪", "weapon",     0,    6,    0,     4,     1,     30,    0.04, 0.02),
                ("Copper Sword", "🗡️", "weapon",            0,    12,   0,     2,     3,     50,    0.03, 0.01),
                ("Copper Armor", "🛡", "armor",              50,   0,    7,     0,    0,      50,    0,    0),
                ("Orc Mace", "🪓", "weapon",                0,    26,   0,     -2,    7,     100,   0.03, 0),
                ("Orc Heart", "🫀", "accessory",            30,   0,    0,     0,     0,     80,    0,    0),
                ("Cursed Bone", "🦴", "weapon",             0,    18,   0,     2,     4,     80,    0.04, 0.01),
                ("Cursed Skull", "💀", "accessory",         0,    6,    0,     0,     1,     80,    0,    0),
                ("Steel Sword", "🗡️", "weapon",             0,    24,   0,     3,     5,     250,   0.05, 0.01),
                ("Steel Armor", "🛡️", "armor",              140,  0,    9,     0,     0,     250,   0,    0),
                ("Bandit Knife", "🔪", "weapon",            0,    17,   0,     7,     2,     300,   0.07, 0.03),
                ("Ninja Suit", "🥷", "armor",               80,   0,    6,     5,     0,     300,   0,    0.02),
                ("Thorn Vine", "🌿", "weapon",              -20,  32,   0,     5,     5,     300,   0.06, 0.02),
                ("Life Bloom", "🌺", "accessory",           50,   0,    1,     0,     0,     300,   0,    0),
                ("Knight Claymore", "🗡️", "weapon",         0,    50,   2,     -3,    10,    600,   0.10, -0.02),
                ("Knight Insignia", "⚜️", "accessory",      30,   1,    4,     0,     0,     600,   0,    0),
                ("Knight Armor", "🛡️", "armor",             180,  0,    13,    -4,    0,     600,   0,    -0.02),
                ("Broken Trident", "🔱", "weapon",          0,    35,   0,     4,     6,     600,   0.07, 0.01),
                ("Sea Prism", "💎", "accessory",            0,    2,    0,     5,     2,     600,   0,    0)
            ]

            TIERS = {
                "common": {
                    "health_mult": 1,
                    "damage_mult": 1,
                    "armor_mult": 1,
                    "speed_mult": 1,
                    "break_force_mult": 1,
                    "price_mult": 1,
                    "critical_chance_mult": 1,
                    "dodge_chance_mult": 1
                },

                "uncommon": {
                    "health_mult": 1.1,
                    "damage_mult": 1.1,
                    "armor_mult": 1.05,
                    "speed_mult": 1.1,
                    "break_force_mult": 1.1,
                    "price_mult": 1.1,
                    "critical_chance_mult": 1,
                    "dodge_chance_mult": 1
                },

                "rare": {
                    "health_mult": 1.2,
                    "damage_mult": 1.2,
                    "armor_mult": 1.1,
                    "speed_mult": 1.2,
                    "break_force_mult": 1.2,
                    "price_mult": 1.15,
                    "critical_chance_mult": 1.05,
                    "dodge_chance_mult": 1.05
                },

                "epic": {
                    "health_mult": 1.35,
                    "damage_mult": 1.35,
                    "armor_mult": 1.2,
                    "speed_mult": 1.3,
                    "break_force_mult": 1.3,
                    "price_mult": 1.25,
                    "critical_chance_mult": 1.1,
                    "dodge_chance_mult": 1.1
                },

                "legendary": {
                    "health_mult": 1.5,
                    "damage_mult": 1.5,
                    "armor_mult": 1.4,
                    "speed_mult": 1.5,
                    "break_force_mult": 1.5,
                    "price_mult": 1.4,
                    "critical_chance_mult": 1.2,
                    "dodge_chance_mult": 1.2
                }
            }

            valid_keys = []

            # Generate market equipments
            for name, emoji, eq_type, health, dmg, armor, speed, break_force, price, crit, dodge in market_equipments:
                item_id = await items_db.get_or_create_item(name, emoji, "equipment")

                await self.add_equipment(
                    item_id,
                    eq_type,
                    health,
                    dmg,
                    armor,
                    speed,
                    break_force,
                    "common",
                    price,
                    crit,
                    dodge,
                    market_only=True
                )

                valid_keys.append((item_id, "common"))

            # Generate equipments

            for (name, emoji, equipment_type,base_health ,base_damage, base_armor, base_speed, base_break_force, base_price,
                base_critical_chance, base_dodge_chance) in base_equipments:

                item_id = await items_db.get_or_create_item(name, emoji, "equipment")

                for tier, mult in TIERS.items():
                    health = int(base_health * mult["health_mult"])
                    damage = int(base_damage * mult["damage_mult"])
                    armor = int(base_armor * mult["armor_mult"])
                    speed = int(base_speed * mult["speed_mult"])
                    break_force = int(base_break_force * mult["break_force_mult"])
                    price = int(base_price * mult["price_mult"])
                    critical_chance = round(base_critical_chance * mult["critical_chance_mult"], 4)
                    dodge_chance = round(base_dodge_chance * mult["dodge_chance_mult"], 4)

                    await self.add_equipment(
                        item_id,
                        equipment_type,
                        health,
                        damage,
                        armor,
                        speed,
                        break_force,
                        tier,
                        price,
                        critical_chance,
                        dodge_chance
                    )

                    valid_keys.append((item_id, tier))

            # Remove rows not in pool anymore
            async with self.db.cursor() as cursor:

                if valid_keys:
                    placeholders = ",".join(["(?, ?)"] * len(valid_keys))

                    values = [v for pair in valid_keys for v in pair]

                    await cursor.execute(f"""
                        DELETE FROM equipments
                        WHERE (item_id, tier) NOT IN ({placeholders})
                    """, values)
            await self.db.commit()

            # Remove equipments not in base pool
            valid_names = (
                    [e[0] for e in base_equipments] +
                    [e[0] for e in market_equipments]
            )

            if valid_names:

                async with self.db.cursor() as cursor:

                    placeholders = ",".join("?" * len(valid_names))

                    await cursor.execute(f"""
                        DELETE FROM items
                        WHERE item_type='equipment'
                        AND name NOT IN ({placeholders})
                    """, valid_names)

                await self.db.commit()
        except Exception as e:
            print(f"Error generating equipments: {e}")
            raise

    async def ensure_equipments(self, items_db):
        await self.generate_equipments(items_db)