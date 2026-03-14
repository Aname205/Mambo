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
                ("Crude Speed Gem", "💎", "accessory", 0, 0, 0, 2, 0, 1000, 0, 0),
                ("Crude Blood Gem", "🔴", "accessory", 10, 0, 0, 0, 0, 1000, 0, 0),
            ]

            base_equipments = [
                # Fields: name, emoji, equipment_type,      hp,   dmg,  armor, speed, break, price, crit, dodge
                ("Rusty Copper Sword", "🗡️", "weapon",      0,    7,    0,     2,     2,     30,    0.02, 0.01),
                ("Rusty Copper Armor", "🛡", "armor",       30,    0,    4,     0,     0,     30,    0,    0),
                ("Rusty Copper Axe" , "🪓", "weapon",       0,    11,   0,     -1,    4,     30,    0.02, 0),
                ("Rusty Copper Knife" , "🔪", "weapon",     0,    6,    0,     4,     1,     30,    0.04, 0.02),
                ("Copper Sword", "🗡️", "weapon",            0,    12,   0,     2,     3,     50,    0.03, 0.01),
                ("Copper Armor", "🛡", "armor",              50,   0,    7,     0,    0,      50,    0,    0),
                ("Orc Mace", "🪓", "weapon",                0,    26,   0,     -2,    5,     100,   0.03, 0),
                ("Orc Heart", "🫀", "accessory",            30,   0,    0,     0,     0,     80,    0,    0),
                ("Cursed Bone", "🦴", "weapon",             0,    18,   0,     2,     4,     80,    0.04, 0.01),
                ("Cursed Skull", "💀", "accessory",         0,    6,    0,     0,     1,     80,    0,    0),
                ("Steel Sword", "🗡️", "weapon",             0,    24,   0,     2,     4,     250,   0.05, 0.01),
                ("Steel Armor", "🛡️", "armor",              140,  0,    9,     0,     0,     250,   0,    0),
                ("Bandit Knife", "🔪", "weapon",            0,    17,   0,     5,     2,     300,   0.07, 0.03),
                ("Ninja Suit", "🥷", "armor",               80,   0,    6,     4,     0,     300,   0,    0.02),
                ("Thorn Vine", "🌿", "weapon",              -20,  28,   0,     3,     5,     300,   0.06, 0.02),
                ("Life Bloom", "🌺", "accessory",           50,   0,    1,     0,     0,     300,   0,    0),
                ("Knight Claymore", "🗡️", "weapon",         0,    44,   2,     -3,    8,    600,   0.10, -0.02),
                ("Knight Insignia", "⚜️", "accessory",      30,   1,    8,     0,     0,     600,   0,    0),
                ("Knight Armor", "🛡️", "armor",             180,  0,    13,    -4,    0,     600,   0,    -0.02),
                ("Broken Trident", "🔱", "weapon",          0,    32,   0,     3,     5,     600,   0.07, 0.01),
                ("Sea Prism", "💎", "accessory",            0,    6,    0,     3,     2,     600,   0,    0),
                ("Lost Soul", "👻", "accessory",            0,    0,    0,     5,     0,     900,   0,    0.04),
                ("King Club", "🪓", "weapon",               80,   50,   10,    -3,    9,     900,   0.11, -0.03),
                ("Nazar", "🧿", "accessory",                0,    20,   0,     -1,    0,     900,   0.01, 0),
                ("Death Core", "⚫", "accessory",           -50,  0,    20,    0,     6,     1500,  0,    0.03),
                ("Death Whip", "🌿", "weapon",              -50,  40,   0,     4,     6,     1500,  0.1,  0.04),
                ("Flesh Armor", "🥩", "armor",              300,  0,    24,    1,     0,     1500,  0,    0.02),
                ("Rotten Meat", "🍖", "accessory",          120,  0,    5,     1,     0,     1500,  0.02, 0),
                ("Shadow Coat", "🥷", "armor",              200,  0,    15,    8,     0,     2000,  0.03, 0.05),
                ("Black Knife", "🔪", "weapon",             0,    32,   0,     8,     4,     2000,  0.06, 0.05),
                ("Raptor Claw", "🦷", "accessory",          40,   10,   5,     3,     2,     2000,  0.02, 0.02),
                ("Hour Glass", "⏳", "accessory",           0,    0,    0,     8,     0,     2000,  0,    0.06),
                ("Revert Hour Glass", "⌛", "accessory",    0,    80,   10,    -6,    3,     2000,  0,    -0.03),
                ("Mandible", "🗡️", "weapon",                0,    60,   0,     5,     5,     2000,  0.08, 0),
                ("Ice Cage", "🛡️", "armor",                 200,  0,    75,    0,     0,     2000,  0,    0),
                ("Imbued Ice Cube", "🧊", "weapon",         0,    35,   0,     5,     12,    2000,  0.1,  0.1),
                ("The Eye", "👁️", "accessory",              0,    0,    0,     0,     0,     3000,  0.15, 0),
                # Fields: name, emoji, equipment_type,      hp,   dmg,  armor, speed, break, price, crit, dodge
                ("Void Fang", "🦷", "weapon",               0,    75,   0,     6,     6,     2600,  0.12, 0.05),
                ("Abyss Cloak", "🕶️", "armor",              250,  0,    22,    10,    0,     2600,  0,    0.08),
                ("Soul Lantern", "🏮", "accessory",         200,  0,    0,     3,     0,     2600,  0,    0.03),
                ("Bone Colossus Hammer", "🔨", "weapon",    80,   120,  10,    -4,   10,     3000,  0.10, -0.02),
                ("Ghoul Claw", "🦴", "weapon",              0,    65,   0,     8,     5,     2800,  0.13, 0.06),
                ("Necromancer Robe", "🧥", "armor",         180,  0,    14,    8,     10,    2800,  0,    0.10),
                ("Plague Dagger", "🔪", "weapon",           0,    75,   0,     9,     4,     3000,  0.18, 0.10),
                ("Plague", "💉", "accessory",               -100, 50,   -20,   5,     4,     3000,  0.05, 0.05),
                ("Cultist Mask", "🎭", "accessory",         180,  35,   0,     0,     8,     3000,  0.08, 0.04),
                ("Gargoyle Armor", "🛡️", "armor",           500,  0,    50,    -2,    0,     3500,  0,    -0.02),
                ("Stone Sigil", "🗿", "accessory",          0,    0,    30,    0,     0,     3500,  0,    0),
                ("Cave Fang Blade", "🗡️", "weapon",         0,    100,  0,     6,     10,    3400,  0.12, 0.05),
                ("Blood Ritual Knife", "🔪", "weapon",      -50,  100,  0,     12,    5,     3800,  0.20, 0.10),
                ("Ritual Robe", "🧥", "armor",              300,  0,    32,    12,    0,     3800,  0.1,  0.15),
                ("Blood Pendant", "🩸", "accessory",        400,  0,    0,     0,     0,     3800,  0.05, 0),
                ("Bone Crusher", "🔨", "weapon",            0,    200,  0,     -5,    15,    3800,  0.15, 0),
                ("Serpent Spear", "🔱", "weapon",           0,    110,  0,     10,    10,    4200,  0.15, 0.10),
                ("Heart Of The Sea", "🩵", "accessory",     50,   50,   50,    0,     0,     4200,  0.1,  0.1),
                # Fields: name, emoji, equipment_type,      hp,   dmg,  armor, speed, break, price, crit, dodge
                ("Dread Knight Greatsword", "⚔️", "weapon", 0,    180,  15,    0,     12,    5000,  0.2,  0),
                ("Dread Plate", "🛡️", "armor",              800,  0,    80,   -6,     0,     5000,  0,    -0.03),
                ("Soul Eater", "🌀", "accessory",           -300, 0,    0,     0,     15,    5500,  0.20, 0.10),
                ("Soul Phaser", "🥷", "armor",              400,  0,    40,    15,    0,     5500,  0.12, 0.17),
                ("Titan Bone", "🦴", "accessory",           650,  0,    30,    -4,    0,     5500,  0,    -0.02),
                # NETHER / VOID
                ("Nether Edge", "🗡️", "weapon",             0,    165,  0,     12,    7,     6000,  0.22, 0.12),
                ("Void Crown", "👑", "accessory",           0,    60,   15,    6,     0,     6000,  0.10, 0.08),
                # CRYSTAL
                ("Crystal Halberd", "🔱", "weapon",         0,    180,  10,    4,     12,    6500,  0.18, 0.05),
                ("Crystal Guard", "🛡️", "armor",            700,  0,    75,    -3,    0,     6500,  0,    0),
                # LICH
                ("Lich Staff", "🪄", "weapon",              0,    200,  0,     8,     10,    7000,  0.25, 0.12),
                ("Phylactery", "💀", "accessory",           300,  40,   20,    0,     0,     7000,  0.08, 0.05),
                # FROST
                ("Frozen Colossus Axe", "🪓", "weapon",     200,  240,  20,    -8,    14,    9000,  0.15, -0.04),
                ("Frost Titan Armor", "❄️", "armor",        1200, 0,    120,   -6,    0,     9000,  0,    0),
                # ABYSS OVERLORD
                ("Abyss Overlord Blade", "⚔️", "weapon",    0,    260,  25,    6,     15,    10000, 0.28, 0.12),
                ("Overlord Sigil", "🔮", "accessory",       100,  100,  10,    10,    10,    10000, 0.10, 0.10),

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
                    "health_mult": 1.4,
                    "damage_mult": 1.2,
                    "armor_mult": 1.2,
                    "speed_mult": 1.1,
                    "break_force_mult": 1.1,
                    "price_mult": 2,
                    "critical_chance_mult": 1.05,
                    "dodge_chance_mult": 1.05
                },

                "rare": {
                    "health_mult": 1.8,
                    "damage_mult": 1.5,
                    "armor_mult": 1.5,
                    "speed_mult": 1.2,
                    "break_force_mult": 1.2,
                    "price_mult": 3,
                    "critical_chance_mult": 1.1,
                    "dodge_chance_mult": 1.1
                },

                "epic": {
                    "health_mult": 2.4,
                    "damage_mult": 1.8,
                    "armor_mult": 1.8,
                    "speed_mult": 1.3,
                    "break_force_mult": 1.3,
                    "price_mult": 5,
                    "critical_chance_mult": 1.2,
                    "dodge_chance_mult": 1.2
                },

                "legendary": {
                    "health_mult": 3.2,
                    "damage_mult": 2.4,
                    "armor_mult": 2.5,
                    "speed_mult": 1.5,
                    "break_force_mult": 1.5,
                    "price_mult": 20,
                    "critical_chance_mult": 1.4,
                    "dodge_chance_mult": 1.4
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