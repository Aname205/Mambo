import random

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
                    exp_min INTEGER DEFAULT 0,
                    exp_max INTEGER DEFAULT 0,
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
        exp_min=0,
        exp_max=0,
        monster_modifier="normal",
        loot_table_id=None
    ):
        async with self.db.cursor() as cursor:
            # Upsert by name (case-insensitive): update if exists, otherwise insert.
            await cursor.execute(
                "SELECT monster_id FROM monsters WHERE name = ? COLLATE NOCASE",
                (name,)
            )
            existing = await cursor.fetchone()

            if existing:
                monster_id = existing[0]
                await cursor.execute("""
                    UPDATE monsters
                    SET
                        name = ?,
                        health = ?,
                        damage = ?,
                        armor = ?,
                        tenacity = ?,
                        speed = ?,
                        critical_chance = ?,
                        dodge_chance = ?,
                        level = ?,
                        currency_reward = ?,
                        exp_min = ?,
                        exp_max = ?,
                        monster_modifier = ?,
                        loot_table_id = ?
                    WHERE monster_id = ?
                """, (
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
                    exp_min,
                    exp_max,
                    monster_modifier,
                    loot_table_id,
                    monster_id,
                ))
            else:
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
                        exp_min,
                        exp_max,
                        monster_modifier,
                        loot_table_id
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
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
                    exp_min,
                    exp_max,
                    monster_modifier,
                    loot_table_id,
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

    async def get_random_monster_by_level(self, monster_level):
        async with self.db.cursor() as cursor:
            await cursor.execute("""
                SELECT monster_id, monster_modifier
                FROM monsters
                WHERE level <= ?
                """, (monster_level,))
            all_monsters_by_level = await cursor.fetchall()

        if not all_monsters_by_level:
            return None

        weights_map = {
            "normal": 77,
            "mystic": 8,
            "brutal": 6,
            "chaos": 5,
            "giant": 4
        }

        weights = [weights_map.get(m[1], 10) for m in all_monsters_by_level]
        selected_id = random.choices(all_monsters_by_level, weights=weights, k=1)[0][0]

        return await self.get_monster(selected_id)

    async def generate_monsters(self, loot_tables):


        BASE_MONSTERS = [
            # Fields: name,     hp,     dmg,    armor, tenacity, speed, crit, dodge, level, currency_reward, exp_min, exp_max
            ("Slime",           45,     4,      0,     8,        5,     0.02, 0.05,  1,     30,              15,      25),
            ("Goblin",          75,     7,      2,     12,       6,     0.05, 0.07,  2,     50,              30,      50),
            ("Wolf",            100,    9,      2,     16,       10,    0.06, 0.10,  3,     80,              45,      75),
            ("Orc",             220,    15,     5,     25,       6,     0.08, 0.05,  4,     150,             85,      140),
            ("Skeleton",        150,    12,     4,     15,       9,     0.05, 0.07,  4,     150,             70,      115),
            ("Bandit",          200,    15,     4,     18,       12,    0.08, 0.08,  5,     300,             95,      160),
            ("Venus Fly Trap",  300,    20,     3,     25,       8,     0.08, 0.01,  5,     300,             130,     215),
            ("Cursed Knight",   550,    22,     8,     35,       8,     0.06, 0.05,  6,     600,             210,     350),
            ("Drowned",         380,    18,     6,     25,       12,    0.09, 0.06,  6,     600,             165,     275),
            ("Arthropleura",    2000,   48,     35,    75,      15,    0.10, 0.08,  10,    5000,            900,     1500)
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
                "reward": 1,
                "exp": 1.0
            },

            "mystic": {
                "health": 1.6,
                "damage": 1.2,
                "armor": 1.2,
                "speed": 1.2,
                "tenacity": 2.5,
                "crit": 1.8,
                "dodge": 1.8,
                "reward": 2.5,
                "exp": 2.0
            },

            "brutal": {
                "health": 2.2,
                "damage": 2.2,
                "armor": 1.2,
                "speed": 1.2,
                "tenacity": 1.5,
                "crit": 2.0,
                "dodge": 1.0,
                "reward": 2.5,
                "exp": 2.5
            },

            "chaos": {
                "health": 2.0,
                "damage": 1.5,
                "armor": 1.5,
                "speed": 1.8,
                "tenacity": 1.0,
                "crit": 1.5,
                "dodge": 2.0,
                "reward": 3.0,
                "exp": 2.8
            },

            "giant": {
                "health": 3.5,
                "damage": 2.0,
                "armor": 2.5,
                "speed": 0.6,
                "tenacity": 3.5,
                "crit": 1.5,
                "dodge": 0.5,
                "reward": 3.5,
                "exp": 3.2
            }
        }

        valid_ids = []

        for name, health, dmg, armor, tenacity, speed, crit, dodge, level, reward, exp_min, exp_max in BASE_MONSTERS:

            for modifier, mult in MONSTER_MODIFIERS.items():
                new_health = int(health * mult["health"])
                new_dmg = int(dmg * mult["damage"])
                new_armor = int(armor * mult["armor"])
                new_speed = int(speed * mult["speed"])
                new_tenacity = int(tenacity * mult["tenacity"])

                new_crit = round(crit * mult["crit"], 4)
                new_dodge = round(dodge * mult["dodge"], 4)

                new_reward = int(reward * mult["reward"])
                new_exp_min = int(exp_min * mult["exp"])
                new_exp_max = int(exp_max * mult["exp"])

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
                    new_exp_min,
                    new_exp_max,
                    modifier,
                    loot_table_id
                )

                valid_ids.append(monster_id)

