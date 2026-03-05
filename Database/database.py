import aiosqlite

class Database:
    def __init__(self, bot):
        self.bot = bot
        self.db = None

    async def connect(self):
        self.db = await aiosqlite.connect("../database.db")
        await self.db.execute("PRAGMA foreign_keys = ON")
        await self.create_tables()

    async def create_tables(self):
        async with self.db.cursor() as cursor:
            await cursor.execute("""
            CREATE TABLE IF NOT EXISTS Mambo(
                user INTEGER PRIMARY KEY,
                wallet INTEGER,
                bank INTEGER
            )
            """)

            await cursor.execute("""
            CREATE TABLE IF NOT EXISTS items(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                emoji TEXT
            )
            """)

            await cursor.execute("""
            CREATE TABLE IF NOT EXISTS inventories(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                item_id INTEGER,
                FOREIGN KEY (item_id) REFERENCES items(id)
            )
            """)

            await cursor.execute("""
            CREATE TABLE IF NOT EXISTS fishing_items(
                id INTEGER PRIMARY KEY,
                price INTEGER,
                tier TEXT,
                fishing_rate REAL,
                description TEXT,
                FOREIGN KEY (id) REFERENCES items(id)
            )
            """)

            await cursor.execute("""
            CREATE TABLE IF NOT EXISTS market_items(
                id INTEGER PRIMARY KEY,
                price INTEGER,
                description TEXT,
                FOREIGN KEY (id) REFERENCES items(id)
            )
            """)

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