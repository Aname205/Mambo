class BalanceDB:
    def __init__(self, db):
        self.db = db

    async def create_table(self):
        async with self.db.cursor() as cursor:
            await cursor.execute("""CREATE TABLE IF NOT EXISTS balance(
                user_id INTEGER PRIMARY KEY,
                in_hand INTEGER DEFAULT 1000,
                in_bank INTEGER DEFAULT 0
            )""")
        await self.db.commit()

    async def create_balance(self, user_id):
        async with self.db.cursor() as cursor:
            await cursor.execute(
                "INSERT INTO balance(user_id, in_hand, in_bank) VALUES(?, ?, ?)",
                (user_id, 1000, 0)
            )
        await self.db.commit()

    async def get_balance(self, user_id):
        async with self.db.cursor() as cursor:
            await cursor.execute(
                "SELECT in_hand, in_bank FROM balance WHERE user_id = ?",
                (user_id,)
            )
            data = await cursor.fetchone()

        if data is None:
            await self.create_balance(user_id)
            return 1000, 0

        return data

    async def update_wallet(self, user_id, amount):
        """Cộng/trừ tiền trong wallet. amount dương = cộng, âm = trừ"""
        await self.get_balance(user_id)
        async with self.db.cursor() as cursor:
            await cursor.execute(
                "UPDATE balance SET in_hand = in_hand + ? WHERE user_id = ?",
                (amount, user_id)
            )
        await self.db.commit()

    async def update_bank(self, user_id, amount):
        """Cộng/trừ tiền trong bank. amount dương = cộng, âm = trừ"""
        await self.get_balance(user_id)
        async with self.db.cursor() as cursor:
            await cursor.execute(
                "UPDATE balance SET in_bank = in_bank + ? WHERE user_id = ?",
                (amount, user_id)
            )
        await self.db.commit()

