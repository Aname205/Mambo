class MonsterDB:
    def __init__(self, db):
        self.db = db

    async def create_table(self):
        async with self.db.cursor() as cursor:
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS monsters(
                    monster_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    health INTEGER NOT NULL,        
                    damage INTEGER NOT NULL,
                    armor INTEGER DEFAULT 0,
                    tenacity INTEGER DEFAULT 0,
                    speed INTEGER DEFAULT 5,
                    critical_chance INTEGER DEFAULT 0,
                    dodge_chance INTEGER DEFAULT 0,
                    level INTEGER DEFAULT 1,
                    currency_reward INTEGER DEFAULT 0,
                    monster_modifier TEXT DEFAULT 'normal',
                    loot_table_id INTEGER,
                    FOREIGN KEY (loot_table_id) REFERENCES loot_tables(id)
                )
            """)
        await self.db.commit()

    async def add_monster(
        self,
        name,
        health,
        damage,
        armor=0,
        tenacity=0,
        speed=5,
        critical_chance=0,
        dodge_chance=0,
        level=1,
        currency_reward=0,
        monster_modifier="normal",
        loot_table_id=None
    ):
        async with self.db.cursor() as cursor:
            await cursor.execute("""
                INSERT INTO monsters(
                    name, 
                    health, 
                    damage, 
                    armor,
                    tenacity, 
                    speed,
                    critical_chance,
                    dodge_chance,
                    level, 
                    currency_reward,
                    monster_modifier, 
                    loot_table_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,(
                name,
                health,
                damage,
                armor,
                tenacity,
                speed,
                critical_chance,
                dodge_chance,
                level,
                currency_reward,
                monster_modifier,
                loot_table_id
            ))

            monster_id = cursor.lastrowid

        await self.db.commit()
        return monster_id

    async def get_monster(self, monster_id):
        async with self.db.cursor() as cursor:
            await cursor.execute("""
                SELECT * FROM monsters 
                WHERE monster_id = ?""", (monster_id,))

            monster = await cursor.fetchone()

        return monster

    async def get_monster_by_name(self, monster_name):
        async with self.db.cursor() as cursor:
            await cursor.execute("""
                SELECT * FROM monsters 
                WHERE name = ?""", (monster_name,))

            monster = await cursor.fetchone()

        return monster

    async def get_monster_by_level(self, monster_level):
        async with self.db.cursor() as cursor:
            await cursor.execute("""
                SELECT * FROM monsters 
                WHERE level = ?""", (monster_level,))

            monster = await cursor.fetchone()

        return monster

    async def get_all_monsters(self):
        async with self.db.cursor() as cursor:
            await cursor.execute("""SELECT * FROM monsters """)

            monsters = await cursor.fetchall()

        return monsters

    async def update_monster(self, monster_id, **kwargs):
        if not kwargs:
            return

        fields = []
        values = []

        for key, value in kwargs.items():
            fields.append(f"{key} = ?")
            values.append(value)

        values.append(monster_id)

        query = f"""
            UPDATE monsters 
            SET {', '.join(fields)} 
            WHERE monster_id = ?"""

        async with self.db.cursor() as cursor:
            await cursor.execute(query, tuple(values))

        await self.db.commit()

    async def get_random_monster(self):
        async with self.db.cursor() as cursor:
            await cursor.execute("SELECT monster_id, monster_modifier FROM monsters")
            all_monsters = await cursor.fetchall()

        if not all_monsters:
            return None

        import random
        weights_map = {
            "normal": 88,
            "mystic": 3,
            "brutal": 3,
            "chaos": 3,
            "giant": 3
        }
        
        weights = [weights_map.get(m[1], 10) for m in all_monsters]
        selected_id = random.choices(all_monsters, weights=weights, k=1)[0][0]

        return await self.get_monster(selected_id)

    async def generate_monsters(self, loot_tables):

        # Fields: name, hp, dmg, armor, tenacity, speed, crit, dodge, level, currency_reward
        BASE_MONSTERS = [
            ("Slime", 40, 4, 0, 4, 5, 0.02, 0.05, 1, 20),
            ("Goblin", 60, 7, 2, 7, 6, 0.05, 0.07, 2, 40),
            ("Wolf", 80, 9, 2, 12, 10, 0.06, 0.10, 3, 60),
            ("Orc", 200, 15, 5, 20, 4, 0.08, 0.05, 5, 120),
        ]


        MONSTER_MODIFIERS = {
            "normal": {
                "health": 1,
                "damage": 1,
                "armor": 1,
                "speed": 1,
                "tenacity": 1,
                "crit": 1,
                "dodge": 1,
                "reward": 1
            },

            "mystic": {
                "health": 1.8,
                "damage": 1.2,
                "armor": 1.2,
                "speed": 1.2,
                "tenacity": 2.5,
                "crit": 1.8,
                "dodge": 1.8,
                "reward": 2.5
            },

            "brutal": {
                "health": 1.8,
                "damage": 2.5,
                "armor": 1.2,
                "speed": 1.2,
                "tenacity": 1.2,
                "crit": 2.0,
                "dodge": 1.0,
                "reward": 2.5
            },

            "chaos": {
                "health": 2.0,
                "damage": 1.5,
                "armor": 1.5,
                "speed": 2.5,
                "tenacity": 1.5,
                "crit": 1.5,
                "dodge": 2.5,
                "reward": 3.0
            },

            "giant": {
                "health": 3.5,
                "damage": 1.8,
                "armor": 2.5,
                "speed": 0.6,
                "tenacity": 1.5,
                "crit": 1.2,
                "dodge": 0.5,
                "reward": 3.5
            }
        }

        valid_ids = []

        for name, health, dmg, armor, tenacity, speed, crit, dodge, level, reward in BASE_MONSTERS:

            for modifier, mult in MONSTER_MODIFIERS.items():
                new_health = int(health * mult["health"])
                new_dmg = int(dmg * mult["damage"])
                new_armor = int(armor * mult["armor"])
                new_speed = int(speed * mult["speed"])
                new_tenacity = int(tenacity * mult["tenacity"])

                new_crit = round(crit * mult["crit"], 4)
                new_dodge = round(dodge * mult["dodge"], 4)

                new_reward = int(reward * mult["reward"])

                monster_name = f"{modifier.capitalize()} {name}"

                loot_table_id = loot_tables.get(name)

                monster_id = await self.add_monster(
                    monster_name,
                    new_health,
                    new_dmg,
                    new_armor,
                    new_tenacity,
                    new_speed,
                    new_crit,
                    new_dodge,
                    level,
                    new_reward,
                    modifier,
                    loot_table_id
                )

                valid_ids.append(monster_id)

    async def ensure_monsters(self):
        monsters = await self.get_all_monsters()
        if not monsters:
            await self.generate_monsters()
