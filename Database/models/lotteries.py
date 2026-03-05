class LotteriesDB:
    def __init__(self, db):
        self.db = db

    async def create_table(self):
        async with self.db.cursor() as cursor:
            await cursor.execute("""
        CREATE TABLE IF NOT EXISTS lotteries(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            enrol_price INTEGER,
            total_price INTEGER,
            winning_number INTEGER,
            start_date DATETIME,
            end_date DATETIME
        )
        """)
        await self.db.commit()
