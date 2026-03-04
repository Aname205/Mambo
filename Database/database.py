import aiosqlite

class Database:
    def __init__(self, bot):
        self.bot = bot
        self.db = None

    async def connect(self):
        self.db = await aiosqlite.connect("../MyBank.db")
        await self.create_tables()

    async def create_tables(self):
        async with self.db.cursor() as cursor:
            await cursor.execute("""CREATE TABLE IF NOT EXISTS Mambo(
                wallet INTEGER,
                bank INTEGER,
                user INTEGER PRIMARY KEY)
            """)
        await self.db.commit()

    async def create_balance(self, user_id):
        async with self.db.cursor() as cursor:
            await cursor.execute(
                "INSERT INTO Mambo(wallet, bank, user) VALUES(?, ?, ?)",
                (100, 0, user_id)
            )
        await self.db.commit()

    async def get_balance(self, user_id):
        async with self.db.cursor() as cursor:
            await cursor.execute(
                "SELECT wallet, bank FROM Mambo WHERE user = ?",
                (user_id,)
            )
            data = await cursor.fetchone()

        if data is None:
            await self.create_balance(user_id)
            return 100, 0

        return data