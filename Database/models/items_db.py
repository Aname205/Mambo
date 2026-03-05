class ItemsDB:
    def __init__(self, db):
        self.db = db

    async def create_table(self):
        async with self.db.cursor() as cursor:
            await cursor.execute("""CREATE TABLE IF NOT EXISTS items(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                emoji TEXT
            )""")
        await self.db.commit()

    async def get_item(self, item_id):
        async with self.db.cursor() as cursor:
            await cursor.execute(
                "SELECT * FROM items WHERE id = ?",
                (item_id,)
            )
            return await cursor.fetchone()

    async def get_all_items(self):
        async with self.db.cursor() as cursor:
            await cursor.execute("SELECT * FROM items")
            return await cursor.fetchall()

    async def add_item(self, name, emoji):
        async with self.db.cursor() as cursor:
            await cursor.execute(
                "INSERT INTO items(name, emoji) VALUES(?, ?)",
                (name, emoji)
            )
        await self.db.commit()

