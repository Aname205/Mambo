class MarketItemsDB:
    def __init__(self, db):
        self.db = db

    async def create_table(self):
        async with self.db.cursor() as cursor:
            await cursor.execute("""
        CREATE TABLE IF NOT EXISTS market_items(
            id INTEGER PRIMARY KEY,
            price INTEGER,
            description TEXT,
            FOREIGN KEY (id) REFERENCES items(id)
        )
        """)
        await self.db.commit()
