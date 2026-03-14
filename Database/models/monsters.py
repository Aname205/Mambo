import random

from Database.data.monster_data import BASE_MONSTERS, MONSTER_MODIFIERS

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
