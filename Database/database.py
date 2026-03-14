import aiosqlite
from Database.models import (BalanceDB, ItemsDB, FishingItemsDB, InventoriesDB, LotteriesDB,
                             LotteryPlayersDB, MarketItemsDB, PlayersDB, EquipmentsDB,
                             MonsterDB, BattleLogsDB, PvpLogsDB, LootTablesDB, LootTableItemsDB)


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
        self.pvp_logs = None
        self.loot_tables = None
        self.loot_table_items = None

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
        self.pvp_logs = PvpLogsDB(self.db)
        self.loot_tables = LootTablesDB(self.db)
        self.loot_table_items = LootTableItemsDB(self.db)

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
        await self.pvp_logs.create_table()
        await self.loot_tables.create_table()
        await self.loot_table_items.create_table()

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

    # Market shortcuts
    async def get_market_equipments(self):
        return await self.market_items.get_market_equipments()

    # Inventory shortcuts
    async def get_inventory(self, user_id):
        return await self.inventories.get_inventory(user_id)

    async def add_to_inventory(self, user_id, item_id, item_tier, amount):
        return await self.inventories.add_to_inventory(user_id, item_id, item_tier, amount)

    async def remove_from_inventory(self, user_id, item_id, item_tier, amount):
        return await self.inventories.remove_from_inventory(user_id, item_id, item_tier, amount)

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

    async def get_equipped_items(self, user_id):
        return await self.players.get_equipped_items(user_id)

    async def add_exp(self, user_id, amount):
        return await self.players.add_exp(user_id, amount)

    async def exp_required(self, level):
        return self.players.exp_required(level)

    # Equipment shortcuts
    async def add_equipment(
            self,
            item_id,
            equipment_type,
            health=0,
            damage=0,
            armor=0,
            speed=0,
            break_force=0,
            tier="common",
            price=0,
            critical_chance=0,
            dodge_chance=0,
            market_only=0
    ):
        return await self.equipments.add_equipment(
            item_id,
            equipment_type,
            health,
            damage,
            armor,
            speed,
            break_force,
            tier,
            price,
            critical_chance,
            dodge_chance,
            market_only
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
            critical_chance=0,
            dodge_chance=0,
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
            critical_chance,
            dodge_chance,
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

    async def generate_monsters(self):
        return await self.monsters.generate_monsters()

    async def get_random_monster(self):
        return await self.monsters.get_random_monster()

    async def get_random_monster_by_level(self, monster_level):
        return await self.monsters.get_random_monster_by_level(monster_level)

    async def ensure_monsters(self):
        """Always upsert loot tables and monsters to ensure data is up-to-date."""
        # Generate/update loot tables first (returns mapping for monster generation)
        loot_tables = await self.loot_tables.generate_default_loot_tables(
            self.loot_table_items
        )
        # Generate/update monsters with loot table references
        await self.monsters.generate_monsters(loot_tables)

    # Battle log shortcuts
    async def start_battle(
            self,
            user_id,
            monster_id,
            player_health,
            player_damage,
            player_armor,
            player_speed,
            player_break_force,
            player_critical_chance,
            player_dodge_chance,
            monster_health,
            monster_damage,
            monster_armor,
            monster_tenacity,
            monster_speed,
            monster_critical_chance,
            monster_dodge_chance,
            monster_level,
            monster_currency_reward,
            monster_exp_min,
            monster_exp_max,
            monster_modifier,
            monster_loot_table_id
    ):
        return await self.battle_logs.start_battle(
            user_id,
            monster_id,
            player_health,
            player_damage,
            player_armor,
            player_speed,
            player_break_force,
            player_critical_chance,
            player_dodge_chance,
            monster_health,
            monster_damage,
            monster_armor,
            monster_tenacity,
            monster_speed,
            monster_critical_chance,
            monster_dodge_chance,
            monster_level,
            monster_currency_reward,
            monster_exp_min,
            monster_exp_max,
            monster_modifier,
            monster_loot_table_id
        )

    async def get_active_battle(self, battle_id):
        return await self.battle_logs.get_active_battle(battle_id)

    async def update_battle_state(self, battle_id, player_health, monster_health, turn_number):
        return await self.battle_logs.update_battle_state(
            battle_id,
            player_health,
            monster_health,
            turn_number
        )

    async def end_battle(self, battle_id, status):
        return await self.battle_logs.end_battle(battle_id, status)

    # Pvp log shortcuts
    async def start_pvp_battle(
            self,
            player_1,
            player_2,
            player_1_health,
            player_2_health,
            player_1_damage,
            player_2_damage,
            player_1_armor,
            player_2_armor,
            player_1_speed,
            player_2_speed,
            player_1_critical_chance,
            player_2_critical_chance,
            player_1_dodge_chance,
            player_2_dodge_chance
    ):
        return await self.pvp_logs.start_pvp_battle(
            player_1,
            player_2,
            player_1_health,
            player_2_health,
            player_1_damage,
            player_2_damage,
            player_1_armor,
            player_2_armor,
            player_1_speed,
            player_2_speed,
            player_1_critical_chance,
            player_2_critical_chance,
            player_1_dodge_chance,
            player_2_dodge_chance
        )

    async def get_active_pvp_battle(self, battle_id):
        return await self.pvp_logs.get_active_pvp_battle(battle_id)

    async def end_pvp_battle(self, battle_id, status):
        return await self.pvp_logs.end_pvp_battle(battle_id, status)

    # Lottery shortcuts
    async def create_lottery(self, enrol_price, total_price, start_date, end_date):
        return await self.lotteries.create_lottery(enrol_price, total_price, start_date, end_date)

    async def get_active_lottery(self):
        return await self.lotteries.get_active_lottery()

    async def set_winning_number(self, lottery_id, number):
        return await self.lotteries.set_winning_number(lottery_id, number)

    async def update_total_price(self, lottery_id, amount):
        return await self.lotteries.update_total_price(lottery_id, amount)

    async def get_recent_lotteries(self, limit=5):
        return await self.lotteries.get_recent_lotteries(limit)

    # Lottery players shortcuts
    async def add_lottery_player(self, user_id, lottery_id, bet_number):
        return await self.lottery_players.add_player(user_id, lottery_id, bet_number)

    async def get_lottery_player_entry(self, user_id, lottery_id):
        return await self.lottery_players.get_player_entry(user_id, lottery_id)

    async def get_lottery_players(self, lottery_id):
        return await self.lottery_players.get_players_by_lottery(lottery_id)

    async def get_lottery_winners(self, lottery_id, winning_number):
        return await self.lottery_players.get_winners(lottery_id, winning_number)

    async def count_lottery_players(self, lottery_id):
        return await self.lottery_players.count_players(lottery_id)

    # Loot tables shortcuts
    async def get_loot_table(self, loot_table_id):
        return await self.loot_tables.get_loot_table(loot_table_id)

    async def generate_default_loot_tables(self):
        return await self.loot_tables.generate_default_loot_tables()

    # Loot table items shortcuts
    async def add_loot_items(
            self,
            loot_table_id,
            item_id,
            drop_chance,
            min_amount=1,
            max_amount=1
    ):
        return await self.loot_table_items.add_loot_items(
            loot_table_id,
            item_id,
            drop_chance,
            min_amount,
            max_amount
        )

    async def get_loot_items(self, loot_table_id):
        return await self.loot_table_items.get_loot_items(loot_table_id)

    async def roll_loot(self, loot_table_id, modifier, monster_level=1, monster_base_level=1):
        return await self.loot_table_items.roll_loot(loot_table_id, modifier, monster_level, monster_base_level)

