class BattleLogsDB:
    def __init__(self,db):
        self.db = db

    async def create_table(self):
        async with self.db.cursor() as cursor:
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS battle_logs(
                    battle_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    monster_id INTEGER,
                    player_health INTEGER,
                    player_damage INTEGER,
                    player_armor INTEGER,
                    player_speed INTEGER,
                    player_break_force INTEGER,
                    player_critical_chance REAL,
                    player_dodge_chance REAL,
                    monster_health INTEGER,
                    monster_damage INTEGER,
                    monster_armor INTEGER,
                    monster_tenacity INTEGER,
                    monster_speed INTEGER,
                    monster_critical_chance REAL,
                    monster_dodge_chance REAL,
                    monster_level INTEGER,
                    monster_currency_reward INTEGER,
                    monster_exp_min INTEGER DEFAULT 0,
                    monster_exp_max INTEGER DEFAULT 0,
                    monster_modifier TEXT DEFAULT 'normal' CHECK (monster_modifier IN ('normal','mystic','brutal','chaos','giant')),
                    monster_loot_table_id INTEGER,
                    battle_status TEXT DEFAULT 'active' CHECK(battle_status IN ('active', 'won', 'lost', 'fled')),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (monster_id) REFERENCES monsters(monster_id)
                )             
            """)

    async def start_battle(
            self,
            user_id,
            monster_id,
            player_health,
            player_damage,
            player_armor,
            player_speed,
            player_break_force,
            player_critical_chance,
            player_dodge_chance,
            monster_health,
            monster_damage,
            monster_armor,
            monster_tenacity,
            monster_speed,
            monster_critical_chance,
            monster_dodge_chance,
            monster_level,
            monster_currency_reward,
            monster_exp_min,
            monster_exp_max,
            monster_modifier,
            monster_loot_table_id
    ):
        async with self.db.cursor() as cursor:
            await cursor.execute("""
                INSERT INTO battle_logs(
                    user_id,
                    monster_id,
                    player_health,
                    player_damage,
                    player_armor,
                    player_speed,
                    player_break_force,
                    player_critical_chance,
                    player_dodge_chance,
                    monster_health,
                    monster_damage,
                    monster_armor,
                    monster_tenacity,
                    monster_speed,
                    monster_critical_chance,
                    monster_dodge_chance,
                    monster_level,
                    monster_currency_reward,
                    monster_exp_min,
                    monster_exp_max,
                    monster_modifier,
                    monster_loot_table_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,(
                    user_id,
                    monster_id,
                    player_health,
                    player_damage,
                    player_armor,
                    player_speed,
                    player_break_force,
                    player_critical_chance,
                    player_dodge_chance,
                    monster_health,
                    monster_damage,
                    monster_armor,
                    monster_tenacity,
                    monster_speed,
                    monster_critical_chance,
                    monster_dodge_chance,
                    monster_level,
                    monster_currency_reward,
                    monster_exp_min,
                    monster_exp_max,
                    monster_modifier,
                    monster_loot_table_id
                ))
            battle_id = cursor.lastrowid

        await self.db.commit()

        return battle_id

    async def get_active_battle(self, battle_id):
        async with self.db.cursor() as cursor:
            await cursor.execute("""
                SELECT * FROM battle_logs 
                WHERE battle_id = ? 
                """, (battle_id,))

            battle = await cursor.fetchone()

        return battle

    async def end_battle(self, battle_id, status):
        async with self.db.cursor() as cursor:
            await cursor.execute("""
                UPDATE battle_logs
                SET battle_status = ?
                WHERE battle_id = ?
                """, (status, battle_id))

        await self.db.commit()