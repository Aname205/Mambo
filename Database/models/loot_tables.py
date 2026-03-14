import random
from Database.data.loot_data import LOOT_DATA

class LootTablesDB:
    def __init__(self, db):
        self.db = db

    async def create_table(self):
        async with self.db.cursor() as cursor:
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS loot_tables(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    monster_name TEXT UNIQUE
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

    async def _get_or_create_loot_table(self, monster_name):
        """Get existing loot table id or create new one (upsert)."""
        async with self.db.cursor() as cursor:
            await cursor.execute(
                "SELECT id FROM loot_tables WHERE LOWER(monster_name) = LOWER(?)",
                (monster_name,)
            )
            row = await cursor.fetchone()
            if row:
                return row[0]

            await cursor.execute(
                "INSERT INTO loot_tables(monster_name) VALUES (?)",
                (monster_name,)
            )
            await self.db.commit()
            return cursor.lastrowid

    async def _get_item_id(self, item_name):
        """Get item_id by name."""
        async with self.db.cursor() as cursor:
            await cursor.execute(
                "SELECT id FROM items WHERE LOWER(name) = LOWER(?)",
                (item_name,)
            )
            row = await cursor.fetchone()
            return row[0] if row else None

    async def generate_default_loot_tables(self, loot_table_items_db):
        """Generate default loot tables and items, auto-update on restart."""

        tables = {}
        valid_loot_entries = []  # Track (loot_table_id, item_id) for cleanup

        for monster_name, items in LOOT_DATA.items():
            # Get or create loot table
            loot_table_id = await self._get_or_create_loot_table(monster_name)
            tables[monster_name] = loot_table_id

            # Add items to loot table
            for item_name, drop_chance, min_amt, max_amt in items:
                item_id = await self._get_item_id(item_name)
                if item_id:
                    await loot_table_items_db.add_loot_item(
                        loot_table_id, item_id,
                        drop_chance=drop_chance,
                        min_amount=min_amt,
                        max_amount=max_amt
                    )
                    valid_loot_entries.append((loot_table_id, item_id))

        # Remove loot_table_items not in current pool
        if valid_loot_entries:
            async with self.db.cursor() as cursor:
                placeholders = ",".join(["(?, ?)"] * len(valid_loot_entries))
                values = [v for pair in valid_loot_entries for v in pair]
                await cursor.execute(f"""
                    DELETE FROM loot_table_items
                    WHERE (loot_table_id, item_id) NOT IN ({placeholders})
                """, values)
            await self.db.commit()


        return tables
