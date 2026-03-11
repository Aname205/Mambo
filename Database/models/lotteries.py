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

    async def create_lottery(self, enrol_price, total_price, start_date, end_date):
        """Create a new lottery session and return its id."""
        async with self.db.cursor() as cursor:
            await cursor.execute("""
                INSERT INTO lotteries(enrol_price, total_price, winning_number, start_date, end_date)
                VALUES (?, ?, NULL, ?, ?)
            """, (enrol_price, total_price, start_date, end_date))
            lottery_id = cursor.lastrowid
        await self.db.commit()
        return lottery_id

    async def get_active_lottery(self):
        """Get the current active lottery (winning_number is NULL = not drawn yet)."""
        async with self.db.cursor() as cursor:
            await cursor.execute("""
                SELECT * FROM lotteries
                WHERE winning_number IS NULL
                ORDER BY id DESC LIMIT 1
            """)
            return await cursor.fetchone()

    async def set_winning_number(self, lottery_id, number):
        """Set the winning number for a completed draw."""
        async with self.db.cursor() as cursor:
            await cursor.execute("""
                UPDATE lotteries SET winning_number = ? WHERE id = ?
            """, (number, lottery_id))
        await self.db.commit()

    async def update_total_price(self, lottery_id, amount):
        """Increment total_price when a ticket is purchased."""
        async with self.db.cursor() as cursor:
            await cursor.execute("""
                UPDATE lotteries SET total_price = total_price + ? WHERE id = ?
            """, (amount, lottery_id))
        await self.db.commit()

    async def get_recent_lotteries(self, limit=5):
        """Get the last N completed lotteries (for history)."""
        async with self.db.cursor() as cursor:
            await cursor.execute("""
                SELECT * FROM lotteries
                WHERE winning_number IS NOT NULL
                ORDER BY id DESC LIMIT ?
            """, (limit,))
            return await cursor.fetchall()
