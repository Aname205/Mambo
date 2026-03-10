class PlayersDB:
    def __init__(self, db):
        self.db = db

    async def create_table(self):
        async with self.db.cursor() as cursor:
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS players(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    
                    health INTEGER default 10,
                    max_health INTEGER default 10,
                    damage INTEGER default 1,
                    armor INTEGER default 0,
                    speed INTEGER default 10,
                    critical_chance REAL default 0.05,
                    dodge_chance REAL default 0.05,
                    
                    equipped_weapon_id INTEGER,
                    equipped_armor_id INTEGER,
                    equipped_accessory_id INTEGER,
                    FOREIGN KEY (equipped_weapon_id) REFERENCES equipments(id),
                    FOREIGN KEY (equipped_armor_id) REFERENCES equipments(id),
                    FOREIGN KEY (equipped_accessory_id) REFERENCES equipments(id)
                )
            """)
            await self.db.commit()

    async def create_player(self, user_id):
        async with self.db.cursor() as cursor:
            await cursor.execute("""
                INSERT OR IGNORE INTO players(user_id) 
                VALUES(?)""", (user_id,))
        await self.db.commit()

    async def get_player(self, user_id):
        async with self.db.cursor() as cursor:
            await cursor.execute("""
                SELECT * FROM players 
                WHERE user_id = ?""", (user_id,))
            player = await cursor.fetchone()

        if player is None:
            await self.create_player(user_id)
            return await self.get_player(user_id)

        return player

    # Flexible stat update
    async def update_stats(self, user_id, **kwargs):
        if not kwargs:
            return

        fields = []
        values = []

        for key, value in kwargs.items():
            fields.append(f"{key} = ?")
            values.append(value)

        values.append(user_id)

        query = f"""
            UPDATE players
            SET {', '.join(fields)}
            WHERE user_id = ?"""

        async with self.db.cursor() as cursor:
            await cursor.execute(query, tuple(values))

        await self.db.commit()

    # Equip weapon or armor
    async def equip_item(self, user_id, equipment_id, slot):
        if slot not in ["weapon", "armor"]:
            raise ValueError("Slot must be 'weapon' or 'armor'")

        column = "equipped_weapon_id" if slot == "weapon" else "equipped_armor_id"

        async with self.db.cursor() as cursor:
            await cursor.execute(f"""
                UPDATE players
                SET {column} = ?
                WHERE user_id = ?
            """, (equipment_id, user_id))

        await self.db.commit()