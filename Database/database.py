import aiosqlite
from Database.models import (BalanceDB, ItemsDB, FishingItemsDB, InventoriesDB, LotteriesDB,
                             LotteryPlayersDB, MarketItemsDB, PlayersDB, EquipmentsDB, MonsterDB, BattleLogsDB)


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
        self.players = None
        self.equipments = None
        self.monsters = None
        self.battle_logs = None

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
        self.players = PlayersDB(self.db)
        self.equipments = EquipmentsDB(self.db)
        self.monsters = MonsterDB(self.db)
        self.battle_logs = BattleLogsDB(self.db)

        # Create tables
        await self.balance.create_table()
        await self.items.create_table()
        await self.fishing_items.create_table()
        await self.inventories.create_table()
        await self.lotteries.create_table()
        await self.lottery_players.create_table()
        await self.market_items.create_table()
        await self.players.create_table()
        await self.equipments.create_table()
        await self.monsters.create_table()
        await self.battle_logs.create_table()

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

    async def get_or_create_item(self, name, emoji, item_type):
        return await self.items.get_or_create_item(name, emoji, item_type)

    async def clear_all_items(self):
        return await self.items.clear_all_items()

    # Fishing items shortcuts
    async def get_fishing_items(self):
        return await self.fishing_items.get_fishing_items()

    async def add_fishing_item(self, id, price, tier, fishing_rate, description):
        return await self.fishing_items.add_fishing_item(id, price, tier, fishing_rate, description)

    async def ensure_fishing_pool(self):
        return await self.fishing_items.ensure_pool(self.items)

    # Inventory shortcuts
    async def get_inventory(self, user_id):
        return await self.inventories.get_inventory(user_id)

    async def add_to_inventory(self, user_id, item_id, item_tier):
        return await self.inventories.add_to_inventory(user_id, item_id, item_tier)

    async def remove_from_inventory(self, user_id, item_id, amount):
        return await self.inventories.remove_from_inventory(user_id, item_id, amount)

    async def remove_all_from_inventory(self, user_id):
        return await self.inventories.remove_all_from_inventory(user_id)

    async def set_item_lock(self, item_id, is_locked):
        return await self.inventories.set_item_lock(item_id, is_locked)

    # Player shortcuts
    async def get_player(self, user_id):
        return await self.players.get_player(user_id)

    async def update_stats(self, user_id, **kwargs):
        return await self.players.update_stats(user_id, **kwargs)

    async def equip_item(self, user_id, equipment_id, slot):
        return await self.players.equip_item(user_id, equipment_id, slot)

    # Equipment shortcuts
    async def add_equipment(
            self,
            item_id,
            equipment_type,
            damage=0,
            armor=0,
            break_force=0,
            tier="common",
            price=0,
            critical_chance=0,
            dodge_chance=0
    ):
        return await self.equipments.add_equipment(
            item_id,
            equipment_type,
            damage,
            armor,
            break_force,
            tier,
            price,
            critical_chance,
            dodge_chance
        )

    async def get_equipment(self, item_id):
        return await self.equipments.get_equipment(item_id)

    async def get_equipment_by_type(self, equipment_type):
        return await self.equipments.get_equipment_by_type(equipment_type)

    async def get_equipment_by_tier(self, tier):
        return await self.equipments.get_equipment_by_tier(tier)

    async def ensure_equipments(self):
        return await self.equipments.ensure_equipments(self.items)

    # Monster shortcuts
    async def add_monster(
            self,
            name,
            health,
            damage,
            armor=0,
            tenacity=0,
            speed=5,
            level=1,
            currency_reward=0,
            monster_modifier="normal",
            loot_table_id=None
    ):
        return await self.monsters.add_monster(
            name,
            health,
            damage,
            armor,
            tenacity,
            speed,
            level,
            currency_reward,
            monster_modifier,
            loot_table_id
        )

    async def get_monster(self, monster_id):
        return await self.monsters.get_monster(monster_id)

    async def get_monster_by_name(self, monster_name):
        return await self.monsters.get_monster_by_name(monster_name)

    async def get_monster_by_level(self, monster_level):
        return await self.monsters.get_monster_by_level(monster_level)

    async def get_all_monsters(self):
        return await self.monsters.get_all_monsters()

    async def update_monster(self, monster_id, **kwargs):
        return await self.monsters.update_monster(monster_id, **kwargs)

    # Battle log shortcuts
    async def start_battle(
            self,
            user_id,
            monster_id,
            player_health,
            monster_health,
            monster_tenacity,
            monster_speed,
            monster_level
    ):
        return await self.battle_logs.start_battle(
            user_id,
            monster_id,
            player_health,
            monster_health,
            monster_tenacity,
            monster_speed,
            monster_level
        )

    async def get_active_battle(self, user_id):
        return await self.battle_logs.get_active_battle(user_id)

    async def update_battle_state(self, battle_id, player_health, monster_health, turn_number):
        return await self.battle_logs.update_battle_state(
            battle_id,
            player_health,
            monster_health,
            turn_number
        )

    async def end_battle(self, battle_id, status):
        return await self.battle_logs.end_battle(battle_id, status)
