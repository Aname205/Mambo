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
