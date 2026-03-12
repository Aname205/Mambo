import random

class LootTablesDB:
    def __init__(self, db):
        self.db = db

    async def create_table(self):
        async with self.db.cursor() as cursor:
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS loot_tables(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    monster_name TEXT
                )
            """)
        await self.db.commit()

    async def get_loot_table(self, loot_table_id):
        async with self.db.cursor() as cursor:
            await cursor.execute(
                "SELECT * FROM loot_tables WHERE id = ?",
                (loot_table_id,)
            )
            return await cursor.fetchone()

    async def generate_default_loot_tables(self, loot_table_items_db):

        tables = {}

        async with self.db.cursor() as cursor:
            # Slime table
            await cursor.execute("""
                 INSERT INTO loot_tables(monster_name)
                 VALUES ('slime')
                 """)
            slime_loot_table_id = cursor.lastrowid
            tables["Slime"] = slime_loot_table_id

            # Goblin table
            await cursor.execute("""
                 INSERT INTO loot_tables(monster_name)
                 VALUES ('goblin')
                 """)
            goblin_loot_table_id = cursor.lastrowid
            tables["Goblin"] = goblin_loot_table_id

            # Wolf table
            await cursor.execute("""
                 INSERT INTO loot_tables(monster_name)
                 VALUES ('wolf')
                 """)
            wolf_loot_table_id = cursor.lastrowid
            tables["Wolf"] = wolf_loot_table_id

            # Orc table
            await cursor.execute("""
                 INSERT INTO loot_tables(monster_name)
                 VALUES ('orc')
                 """)
            orc_loot_table_id = cursor.lastrowid
            tables["Orc"] = orc_loot_table_id

        await self.db.commit()

        # Add items to the tables
        # Fields: loot_table_id, items_id, ...
        await loot_table_items_db.add_loot_item(slime_loot_table_id, 10, drop_chance=0.2, min_amount=1, max_amount=1)
        await loot_table_items_db.add_loot_item(slime_loot_table_id, 11, drop_chance=0.2, min_amount=1, max_amount=1)
        await loot_table_items_db.add_loot_item(slime_loot_table_id, 12, drop_chance=0.2, min_amount=1, max_amount=1)
        await loot_table_items_db.add_loot_item(slime_loot_table_id, 13, drop_chance=0.2, min_amount=1, max_amount=1)

        await loot_table_items_db.add_loot_item(goblin_loot_table_id, 10, drop_chance=0.2, min_amount=1, max_amount=1)
        await loot_table_items_db.add_loot_item(goblin_loot_table_id, 11, drop_chance=0.2, min_amount=1, max_amount=1)
        await loot_table_items_db.add_loot_item(goblin_loot_table_id, 12, drop_chance=0.2, min_amount=1, max_amount=1)
        await loot_table_items_db.add_loot_item(goblin_loot_table_id, 13, drop_chance=0.2, min_amount=1, max_amount=1)
        await loot_table_items_db.add_loot_item(goblin_loot_table_id, 14, drop_chance=0.1, min_amount=1, max_amount=1)
        await loot_table_items_db.add_loot_item(goblin_loot_table_id, 15, drop_chance=0.1, min_amount=1, max_amount=1)

        await loot_table_items_db.add_loot_item(wolf_loot_table_id, 14, drop_chance=0.2, min_amount=1, max_amount=1)
        await loot_table_items_db.add_loot_item(wolf_loot_table_id, 15, drop_chance=0.2, min_amount=1, max_amount=1)

        await loot_table_items_db.add_loot_item(orc_loot_table_id, 14, drop_chance=0.4, min_amount=1, max_amount=1)
        await loot_table_items_db.add_loot_item(orc_loot_table_id, 15, drop_chance=0.4, min_amount=1, max_amount=1)

        return tables
