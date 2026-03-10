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
                    level INTERGER DEFAULT 1,
                    currency_reward INTEGER DEFAULT 0,
                    monster_modifier TEXT DEFAULT 'normal',
                    loot_table_id INTEGER
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
        level=1,
        currency_reward=0,
        monster_modifier="normal",
        loot_table_id=None
    ):
        async with self.db.cursor() as cursor:
            await cursor.execute("""
                INSERT INTO monsters(
                    name, health, damage, armor,
                    tenacity, speed, level, currency_reward,
                    monster_modifier, loot_table_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                name, health, damage, armor,
                tenacity, speed, level, currency_reward,
                monster_modifier, loot_table_id
            ))

        await self.db.commit()

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
