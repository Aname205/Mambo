class PvpLogsDB:
    def __init__(self, db):
        self.db = db

    async def create_table(self):
        async with self.db.cursor() as cursor:
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS pvp_logs(
                battle_id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_1_id INTEGER,
                player_2_id INTEGER,
            
                player_1_health INTEGER,
                player_2_health INTEGER,
                player_1_damage INTEGER,
                player_2_damage INTEGER,
                player_1_armor INTEGER,
                player_2_armor INTEGER,
                player_1_speed INTEGER,
                player_2_speed INTEGER,
                player_1_critical_chance REAL,
                player_2_critical_chance REAL,
                player_1_dodge_chance REAL,
                player_2_dodge_chance REAL,
            
                battle_status TEXT DEFAULT 'active' CHECK(battle_status IN ('active', 'player_1_won', 'player_2_won')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

    async def start_pvp_battle(
            self,
            player_1_id,
            player_2_id,
            player_1_health,
            player_2_health,
            player_1_damage,
            player_2_damage,
            player_1_armor,
            player_2_armor,
            player_1_speed,
            player_2_speed,
            player_1_critical_chance,
            player_2_critical_chance,
            player_1_dodge_chance,
            player_2_dodge_chance
    ):
        async with self.db.cursor() as cursor:
            await cursor.execute("""
                INSERT INTO pvp_logs(
                    player_1_id,
                    player_2_id,
                    player_1_health,
                    player_2_health,
                    player_1_damage,
                    player_2_damage,
                    player_1_armor,
                    player_2_armor,
                    player_1_speed,
                    player_2_speed,
                    player_1_critical_chance,
                    player_2_critical_chance,
                    player_1_dodge_chance,
                    player_2_dodge_chance
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ? ,?)
                """,(
                    player_1_id,
                    player_2_id,
                    player_1_health,
                    player_2_health,
                    player_1_damage,
                    player_2_damage,
                    player_1_armor,
                    player_2_armor,
                    player_1_speed,
                    player_2_speed,
                    player_1_critical_chance,
                    player_2_critical_chance,
                    player_1_dodge_chance,
                    player_2_dodge_chance
                ))

            battle_id = cursor.lastrowid

        await self.db.commit()
        return battle_id

    async def get_active_pvp_battle(self, battle_id):
        async with self.db.cursor() as cursor:
            await cursor.execute("""
                SELECT * FROM pvp_logs 
                WHERE battle_id = ? AND battle_status = 'active'
                ORDER BY battle_id DESC LIMIT 1
                """, (battle_id,))

            pvp_battle = await cursor.fetchone()

        return pvp_battle

    async def end_pvp_battle(self, battle_id, status):
        async with self.db.cursor() as cursor:
            await cursor.execute("""
                UPDATE pvp_logs
                SET battle_status = ?
                WHERE battle_id = ?
                """, (status, battle_id))

        await self.db.commit()
