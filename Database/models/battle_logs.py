class BattleLogsDB:
    def __init__(self,db):
        self.db = db

    async def create_table(self):
        async with self.db.cursor() as cursor:
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS battle_logs(
                    battle_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    monster_id INTEGER NOT NULL,
                    player_health INTEGER NOT NULL,
                    monster_health INTEGER NOT NULL,
                    monster_tenacity INTEGER NOT NULL,
                    monster_speed INTEGER NOT NULL,
                    monster_level INTEGER NOT NULL,
                    turn_number INTEGER DEFAULT 1,
                    battle_status TEXT DEFAULT 'active' CHECK(battle_status IN ('active', 'won', 'lost', 'fled')),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES players(id),
                    FOREIGN KEY (monster_id) REFERENCES monsters(monster_id)
                )             
            """)

    async def start_battle(
            self,
            user_id,
            monster_id,
            player_health,
            monster_health,
            monster_tenacity,
            monster_speed,
            monster_level
    ):
        async with self.db.cursor() as cursor:
            await cursor.execute("""
                INSERT INTO battle_logs(
                    user_id,
                    monster_id,
                    player_health,
                    monster_health,
                    monster_tenacity,
                    monster_speed,
                    monster_level
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,(
                        user_id,
                        monster_id,
                        player_health,
                        monster_health,
                        monster_tenacity,
                        monster_speed,
                        monster_level
                    ))

            battle_id = cursor.lastrowid

        await self.db.commit()
        return battle_id

    async def get_active_battle(self, user_id):
        async with self.db.cursor() as cursor:
            await cursor.execute("""
                SELECT * FROM battle_logs WHERE user_id = ? AND battle_status = 'active'
                ORDER BY battle_id DESC LIMIT 1
                """, (user_id,))

            battle = await cursor.fetchone()

        return battle

    async def update_battle_state(self, battle_id, player_health, monster_health, turn_number):
        async with self.db.cursor() as cursor:
            await cursor.execute("""
                UPDATE battle_logs 
                SET player_health  = ?, 
                    monster_health = ?, 
                    turn_number    = ?
                WHERE battle_id = ?
                """,(
                        player_health,
                        monster_health,
                        turn_number,
                        battle_id
                    ))

        await self.db.commit()

    async def end_battle(self, battle_id, status):
        async with self.db.cursor() as cursor:
            await cursor.execute("""
                UPDATE battle_logs
                SET battle_status = ?
                WHERE battle_id = ?
                """, (status, battle_id))

        await self.db.commit()