class LotteryPlayersDB:
    def __init__(self, db):
        self.db = db

    async def create_table(self):
        async with self.db.cursor() as cursor:
            await cursor.execute("""
        CREATE TABLE IF NOT EXISTS lottery_players(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            lottery_id INTEGER,
            bet_number INTEGER,
            FOREIGN KEY (lottery_id) REFERENCES lotteries(id)
        )
        """)
        await self.db.commit()

    async def add_player(self, user_id, lottery_id, bet_number):
        """Add a ticket entry for a player."""
        async with self.db.cursor() as cursor:
            await cursor.execute("""
                INSERT INTO lottery_players(user_id, lottery_id, bet_number)
                VALUES (?, ?, ?)
            """, (user_id, lottery_id, bet_number))
        await self.db.commit()

    async def get_player_entry(self, user_id, lottery_id):
        """Check if a user already has a ticket in the current session."""
        async with self.db.cursor() as cursor:
            await cursor.execute("""
                SELECT * FROM lottery_players
                WHERE user_id = ? AND lottery_id = ?
            """, (user_id, lottery_id))
            return await cursor.fetchone()

    async def get_players_by_lottery(self, lottery_id):
        """Get all ticket entries for a given lottery."""
        async with self.db.cursor() as cursor:
            await cursor.execute("""
                SELECT * FROM lottery_players
                WHERE lottery_id = ?
            """, (lottery_id,))
            return await cursor.fetchall()

    async def get_winners(self, lottery_id, winning_number):
        """Get all players who picked the winning number."""
        async with self.db.cursor() as cursor:
            await cursor.execute("""
                SELECT * FROM lottery_players
                WHERE lottery_id = ? AND bet_number = ?
            """, (lottery_id, winning_number))
            return await cursor.fetchall()

    async def count_players(self, lottery_id):
        """Count total participants in a lottery session."""
        async with self.db.cursor() as cursor:
            await cursor.execute("""
                SELECT COUNT(*) FROM lottery_players
                WHERE lottery_id = ?
            """, (lottery_id,))
            row = await cursor.fetchone()
            return row[0] if row else 0
