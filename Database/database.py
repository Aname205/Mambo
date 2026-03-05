import aiosqlite
from Database.models import BalanceDB, ItemsDB


class Database:
    def __init__(self, bot):
        self.bot = bot
        self.db = None
        self.balance = None
        self.items = None

    async def connect(self):
        self.db = await aiosqlite.connect("../MyBank.db")

        # Initialize sub-modules
        self.balance = BalanceDB(self.db)
        self.items = ItemsDB(self.db)

        # Create tables
        await self.balance.create_table()
        await self.items.create_table()

    # ============ SHORTCUT METHODS (để không cần sửa code cũ) ============
    async def get_balance(self, user_id):
        return await self.balance.get_balance(user_id)

    async def update_wallet(self, user_id, amount):
        return await self.balance.update_wallet(user_id, amount)

    async def update_bank(self, user_id, amount):
        return await self.balance.update_bank(user_id, amount)

    async def get_item(self, item_id):
        return await self.items.get_item(item_id)

    async def get_all_items(self):
        return await self.items.get_all_items()

    async def add_item(self, name, emoji):
        return await self.items.add_item(name, emoji)

