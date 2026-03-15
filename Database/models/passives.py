class PassivesDB:
    def __init__(self, db):
        self.db = db

    async def create_table(self):
        async with self.db.cursor() as cursor:
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS passives(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    effect TEXT NOT NULL,
                    emoji TEXT NOT NULL,
                    affix_suffix TEXT NOT NULL,
                    equipment_type TEXT NOT NULL CHECK(equipment_type IN ('weapon', 'armor', 'accessory'))
                )
            """)
        await self.db.commit()

    async def add_passive(self, effect, emoji, affix_suffix, equipment_type):
        async with self.db.cursor() as cursor:
            await cursor.execute("""
                INSERT INTO passives(effect, emoji, affix_suffix, equipment_type)
                VALUES (?, ?, ?, ?)
            """, (effect, emoji, affix_suffix, equipment_type))
            await self.db.commit()
            return cursor.lastrowid

    async def get_passive(self, passive_id):
        async with self.db.cursor() as cursor:
            await cursor.execute("SELECT * FROM passives WHERE id = ?", (passive_id,))
            return await cursor.fetchone()

    async def get_passives_by_type(self, equipment_type):
        async with self.db.cursor() as cursor:
            await cursor.execute(
                "SELECT * FROM passives WHERE equipment_type = ?", (equipment_type,)
            )
            return await cursor.fetchall()

    async def get_all_passives(self):
        async with self.db.cursor() as cursor:
            await cursor.execute("SELECT * FROM passives")
            return await cursor.fetchall()

    async def generate_passives(self):
        from Database.data.passive_data import weapon_passives
        all_passives = weapon_passives  # extend later if armor/accessory passives are added

        async with self.db.cursor() as cursor:
            for effect, emoji, affix_suffix, equipment_type in all_passives:
                await cursor.execute("""
                    INSERT INTO passives(effect, emoji, affix_suffix, equipment_type)
                    SELECT ?, ?, ?, ?
                    WHERE NOT EXISTS (
                        SELECT 1 FROM passives WHERE effect = ? AND equipment_type = ?
                    )
                """, (effect, emoji, affix_suffix, equipment_type, effect, equipment_type))
        await self.db.commit()

    async def ensure_passives(self):
        await self.generate_passives()
