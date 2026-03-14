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
            await cursor.execute("SELECT monster_id, monster_modifier FROM monsters WHERE name NOT LIKE '%Arthropleura%' AND name NOT LIKE '%Yeti%'")
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

    async def get_random_monster_by_min_level(self, min_level):
        """
        Pick a random monster whose base level is >= min_level.
        Used to filter out monsters whose cap (base + 3) can no longer
        reach the player's current level.

        Falls back to all monsters if none qualify (safety net only — should
        not normally happen once the roster covers a wide level range).
        """
        async with self.db.cursor() as cursor:
            await cursor.execute("""
                SELECT monster_id, monster_modifier
                FROM monsters
                WHERE level >= ? AND name NOT LIKE '%Arthropleura%' AND name NOT LIKE '%Yeti%'
                """, (min_level,))
            pool = await cursor.fetchall()

        # Safety fallback: shouldn't happen with a well-populated monster roster
        if not pool:
            async with self.db.cursor() as cursor:
                await cursor.execute("SELECT monster_id, monster_modifier FROM monsters WHERE name NOT LIKE '%Arthropleura%' AND name NOT LIKE '%Yeti%'")
                pool = await cursor.fetchall()

        if not pool:
            return None

        weights_map = {
            "normal": 77,
            "mystic": 8,
            "brutal": 6,
            "chaos": 5,
            "giant": 4
        }

        weights = [weights_map.get(m[1], 10) for m in pool]
        selected_id = random.choices(pool, weights=weights, k=1)[0][0]

        return await self.get_monster(selected_id)

    async def get_random_monster_by_level(self, monster_level):
        async with self.db.cursor() as cursor:
            await cursor.execute("""
                SELECT monster_id, monster_modifier
                FROM monsters
                WHERE level <= ? AND name NOT LIKE '%Arthropleura%' AND name NOT LIKE '%Yeti%'
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

    async def get_random_monster_in_level_range(self, min_level, max_level):
        """
        Pick a random monster whose base level falls within [min_level, max_level].
        Applies modifier rarity weights.

        If no monster is found in the range, expands the window upward first,
        then downward — but NEVER below min_level - 1, so a Slime cannot
        appear as a fallback for a high-level player.
        """
        async with self.db.cursor() as cursor:
            await cursor.execute("""
                SELECT monster_id, monster_modifier
                FROM monsters
                WHERE level >= ? AND level <= ? AND name NOT LIKE '%Arthropleura%' AND name NOT LIKE '%Yeti%'
                """, (min_level, max_level))
            pool = await cursor.fetchall()

        # Progressive fallback: expand range by 1 in each direction per step,
        # but keep a hard floor at max(1, min_level - 1) so we never drop
        # so far that a trivially weak monster type (e.g. Slime) appears.
        if not pool:
            floor = max(1, min_level - 1)
            for expansion in range(1, 6):  # max 5 extra steps
                expanded_min = max(floor, min_level - expansion)
                expanded_max = max_level + expansion
                async with self.db.cursor() as cursor:
                    await cursor.execute("""
                        SELECT monster_id, monster_modifier
                        FROM monsters
                        WHERE level >= ? AND level <= ? AND name NOT LIKE '%Arthropleura%' AND name NOT LIKE '%Yeti%'
                        """, (expanded_min, expanded_max))
                    pool = await cursor.fetchall()
                if pool:
                    break

        if not pool:
            return None

        weights_map = {
            "normal": 77,
            "mystic": 8,
            "brutal": 6,
            "chaos": 5,
            "giant": 4
        }

        weights = [weights_map.get(m[1], 10) for m in pool]
        selected_id = random.choices(pool, weights=weights, k=1)[0][0]

        return await self.get_monster(selected_id)

    async def generate_monsters(self, loot_tables):


        BASE_MONSTERS = [
            # Fields: name,     hp,     dmg,    armor, tenacity, speed, crit, dodge, level, currency_reward, exp_min, exp_max
            ("Slime",           45,     5,      0,     8,        5,     0.02, 0.05,  1,     30,              15,      25),
            ("Goblin",          75,     8,      2,     12,       6,     0.05, 0.07,  2,     50,              30,      50),
            ("Wolf",            100,    12,     2,     16,       10,    0.06, 0.10,  3,     80,              45,      75),
            ("Orc",             220,    18,     5,     25,       6,     0.08, 0.05,  4,     150,             85,      140),
            ("Skeleton",        180,    15,     4,     15,       9,     0.05, 0.07,  4,     150,             70,      115),
            ("Bandit",          250,    18,     4,     18,       12,    0.08, 0.08,  5,     300,             95,      160),
            ("Venus Fly Trap",  400,    22,     3,     25,       8,     0.08, 0.01,  5,     300,             130,     215),
            ("Cursed Knight",   600,    32,     8,     35,       8,     0.06, 0.05,  6,     600,             210,     350),
            ("Drowned",         450,    25,     6,     25,       12,    0.09, 0.06,  6,     600,             165,     275),
            ("Ectoplasm",       900,    22,     0,     200,      30,    0.10, 0.10,  7,     900,             300,     400),
            ("High Orc",        1200,   50,     10,    50,       6,     0.08, 0.01,  7,     900,             300,     400),
            ("Death Root",      1400,   62,     20,    50,       10,    0.05, 0.00,  8,     1500,            500,     700),
            ("Corpse Pile",     2600,   120,    15,    100,      4,     0.00, 0.00,  8,     1500,            500,     700),
            ("Shadow Assassin", 1000,   48,     12,    50,       24,    0.14, 0.12,  9,     2000,            500,     700),
            ("Raptor",          1600,   56,     20,    70,       15,    0.1,  0.08,  9,     2000,            500,     700),
            ("Arthropleura",    4000,   68,     35,    75,       15,    0.10, 0.08,  10,    5000,            600,     800),  #BOSS
            ("Antlion",         2000,   70,     35,    70,       12,    0.1,  0,     10,    3000,            600,     800),
            ("Snowy",           1000,   75,     0,     100,      20,    0.1,  0.3,   10,    3000,            600,     800),
            ("Gazer",           10000,  100,    -80,   150,      5,     0.15, 0,     11,    4000,            750,     900),
            ("Void Crawler",    2800,   85,     25,     80,      18,    0.12, 0.08,  11,    3500,            750,     900),
            ("Abyss Bat",       1600,   70,     10,     60,      28,    0.15, 0.18,  11,    3200,            700,     850),
            ("Bone Golem",      4200,   95,     40,     120,     8,     0.08, 0.03,  12,    4200,            850,     1050),
            ("Ghoul",           2400,   80,     20,     90,      16,    0.10, 0.07,  12,    4000,            800,     1000),
            ("Plague Rat",      2000,   90,     15,     70,      22,    0.14, 0.10,  13,    4500,            900,     1100),
            ("Cultist",         2600,   105,    18,     90,      16,    0.16, 0.06,  13,    4600,            900,     1150),
            ("Stone Gargoyle",  5200,   120,    55,     140,     6,     0.08, 0.03,  14,    5200,            1000,    1300),
            ("Cave Stalker",    3000,   110,    25,     110,     20,    0.15, 0.10,  14,    5000,            1000,    1250),
            ("Blood Priest",    3400,   135,    20,     110,     18,    0.18, 0.07,  15,    6000,            1200,    1500),
            ("Bone Crusher",    6200,   150,    65,     160,     5,     0.10, 0.02,  15,    6200,            1200,    1500),
            ("Abyss Serpent",   4200,   155,    30,     140,     22,    0.18, 0.12,  16,    7000,            1500,    1800),
            ("Dread Knight",    7800,   170,    75,     200,     8,     0.12, 0.03,  16,    7500,            1500,    1900),
            ("Soul Devourer",   5000,   180,    35,     200,     20,    0.20, 0.10,  17,    8200,            1800,    2100),
            ("Grave Titan",     9500,   200,    80,     250,     6,     0.12, 0.02,  17,    8500,            1800,    2200),
            ("Nether Hound",    5600,   210,    35,     180,     24,    0.22, 0.12,  18,    9000,            2100,    2400),
            ("Crystal Guardian",11000,  195,    90,     280,     7,     0.10, 0.03,  18,    9200,            2100,    2500),
            ("Void Reaper",     6500,   230,    45,     200,     22,    0.25, 0.10,  19,    10000,           2500,    2800),
            ("Ancient Lich",    7000,   240,    35,     260,     18,    0.28, 0.12,  19,    11000,           2600,    3000),
            ("Frost Titan",     15000,  300,    120,    400,     6,     0.15, 0.03,  20,    15000,           3500,    4000),
            ("Abyss Overlord",  12000,  320,    80,     350,     14,    0.30, 0.08,  20,    16000,           3500,    4200),

            ("Yeti",            35000,  500,    200,   500,      50,    0.10, 0.10,  20,    100000,          6000,    10000)  #BOSS
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

