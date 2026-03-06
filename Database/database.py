import aiosqlite
from Database.models import BalanceDB, ItemsDB, FishingItemsDB, InventoriesDB, LotteriesDB, LotteryPlayersDB, MarketItemsDB


class Database:
    def __init__(self, bot):
        self.bot = bot
        self.db = None
        self.balance = None
        self.items = None
        self.fishing_items = None
        self.inventories = None
        self.lotteries = None
        self.lottery_players = None
        self.market_items = None

    async def connect(self):
        self.db = await aiosqlite.connect("../database.db")

        # bật foreign key
        await self.db.execute("PRAGMA foreign_keys = ON")

        # Initialize sub-modules
        self.balance = BalanceDB(self.db)
        self.items = ItemsDB(self.db)
        self.fishing_items = FishingItemsDB(self.db)
        self.inventories = InventoriesDB(self.db)
        self.lotteries = LotteriesDB(self.db)
        self.lottery_players = LotteryPlayersDB(self.db)
        self.market_items = MarketItemsDB(self.db)

        # Create tables
        await self.balance.create_table()
        await self.items.create_table()
        await self.fishing_items.create_table()
        await self.inventories.create_table()
        await self.lotteries.create_table()
        await self.lottery_players.create_table()
        await self.market_items.create_table()

    # ============ SHORTCUT METHODS (để không cần sửa code cũ) ============
    async def get_balance(self, user_id):
        return await self.balance.get_balance(user_id)

    async def update_wallet(self, user_id, amount):
        return await self.balance.update_wallet(user_id, amount)

    async def update_bank(self, user_id, amount):
        return await self.balance.update_bank(user_id, amount)

    async def get_item(self, item_id):
        return await self.items.get_item(item_id)

    async def get_item_by_name(self, item_name):
        return await self.items.get_item_by_name(item_name)

    async def get_all_items(self):
        return await self.items.get_all_items()

    async def add_item(self, name, emoji):
        return await self.items.add_item(name, emoji)

    async def get_inventory(self, user_id):
        return await self.inventories.get_inventory(user_id)

    async def clear_all_items(self):
        return await self.items.clear_all_items()

    async def get_fishing_items(self):
        return await self.fishing_items.get_fishing_items()

    async def add_fishing_item(self, id, price, tier, fishing_rate, description):
        return await self.fishing_items.add_fishing_item(id, price, tier, fishing_rate, description)

    async def add_to_inventory(self, user_id, item_id):
        return await self.inventories.add_to_inventory(user_id, item_id)

    async def remove_from_inventory(self, user_id, item_id, amount):
        return await self.inventories.remove_from_inventory(user_id, item_id, amount)

    async def remove_all_from_inventory(self, user_id):
        return await self.inventories.remove_all_from_inventory(user_id)

