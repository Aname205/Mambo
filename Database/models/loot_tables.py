import random

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

        # Define loot table data: monster_name -> [(item_name, drop_chance, min, max), ...]
        LOOT_DATA = {
            "Slime": [
                ("Rusty Copper Sword", 0.4, 1, 1),
                ("Rusty Copper Armor", 0.4, 1, 1),
                ("Rusty Copper Axe", 0.4, 1, 1),
                ("Rusty Copper Knife", 0.4, 1, 1),
            ],
            "Goblin": [
                ("Rusty Copper Sword", 0.4, 1, 1),
                ("Rusty Copper Armor", 0.4, 1, 1),
                ("Rusty Copper Axe", 0.4, 1, 1),
                ("Rusty Copper Knife", 0.4, 1, 1),
                ("Copper Sword", 0.2, 1, 1),
                ("Copper Armor", 0.2, 1, 1),
            ],
            "Wolf": [
                ("Copper Sword", 0.4, 1, 1),
                ("Copper Armor", 0.4, 1, 1),
            ],
            "Orc": [
                ("Copper Sword", 1.8, 1, 1),
                ("Copper Armor", 1.8, 1, 1),
                ("Orc Mace", 1.4, 1, 1),
                ("Orc Heart", 1.4, 1, 1),
            ],

            "Skeleton": [
                ("Copper Sword", 1.8, 1, 1),
                ("Copper Armor", 1.8, 1, 1),
                ("Cursed Bone", 1.4, 1, 1),
                ("Cursed Skull", 1.4, 1, 1),
            ],

            "Bandit": [
                ("Steel Sword", 1.2, 1, 1),
                ("Steel Armor", 1.2, 1, 1),
                ("Bandit Knife", 0.6, 1, 1),
                ("Ninja Suit", 0.6, 1, 1),
            ],

            "Venus Fly Trap": [
                ("Steel Sword", 1.2, 1, 1),
                ("Steel Armor", 1.2, 1, 1),
                ("Thorn Vine", 0.6, 1, 1),
                ("Life Bloom", 0.6, 1, 1),
            ],

            "Cursed Knight": [
                ("Knight Claymore", 0.6, 1, 1),
                ("Knight Insignia", 0.6, 1, 1),
                ("Knight Armor", 0.6, 1, 1),
            ],

            "Drowned": [
                ("Broken Trident", 0.6, 1, 1),
                ("Sea Prism", 0.6, 1, 1),
            ],

            "Ectoplasm": [
                ("Lost Soul", 0.6, 1, 1),
            ],

            "High Orc": [
                ("King Club", 0.6, 1, 1),
                ("Nazar", 0.6, 1, 1),
            ],

            "Death Root": [
                ("Death Core", 0.6, 1, 1),
                ("Death Whip", 0.6, 1, 1),
            ],

            "Corpse Pile": [
                ("Flesh Armor", 0.6, 1, 1),
                ("Rotten Meat", 0.6, 1, 1),
            ],

            "Shadow Assassin": [
                ("Shadow Coat", 0.6, 1, 1),
                ("Black Knife", 0.6, 1, 1),
            ],

            "Raptor": [
                ("Raptor Claw", 0.6, 1, 1),
            ],

            "Antlion": [
                ("Hour Glass", 0.6, 1, 1),
                ("Revert Hour Glass", 0.6, 1, 1),
                ("Mandible", 0.6, 1, 1),
            ],

            "Snowy": [
                ("Ice Cage", 0.6, 1, 1),
                ("Imbued Ice Cube", 0.6, 1, 1),
            ],

            "Gazer": [
                ("The Eye", 0.6, 1, 1),
            ],

            "Void Crawler": [
                ("Void Fang", 0.6, 1, 1),
            ],

            "Abyss Bat": [
                ("Abyss Cloak", 0.6, 1, 1),
                ("Soul Lantern", 0.6, 1, 1),
            ],

            "Bone Golem": [
                ("Bone Colossus Hammer", 0.6, 1, 1),
            ],

            "Ghoul": [
                ("Ghoul Claw", 0.6, 1, 1),
                ("Necromancer Robe", 0.6, 1, 1),
            ],

            "Plague Rat": [
                ("Plague Dagger", 0.6, 1, 1),
                ("Plague", 0.6, 1, 1),
            ],

            "Cultist": [
                ("Cultist Mask", 0.6, 1, 1),
            ],

            "Stone Gargoyle": [
                ("Gargoyle Armor", 0.6, 1, 1),
                ("Stone Sigil", 0.6, 1, 1),
            ],

            "Cave Stalker": [
                ("Cave Fang Blade", 0.6, 1, 1),
            ],

            "Blood Priest": [
                ("Blood Ritual Knife",0.6, 1, 1),
                ("Blood Pendant", 0.6, 1, 1),
                ("Ritual Robe", 0.6, 1, 1),
            ],

            "Bone Crusher": [
                ("Bone Crusher", 0.6, 1, 1),
            ],

            "Abyss Serpent": [
                ("Serpent Spear", 0.6, 1, 1),
                ("Heart Of The Sea", 0.6, 1, 1),
            ],

            "Dread Knight": [
                ("Dread Knight Greatsword", 0.6, 1, 1),
                ("Dread Plate", 0.6, 1, 1),
            ],

            "Soul Devourer": [
                ("Soul Eater", 0.6, 1, 1),
                ("Soul Phaser", 0.6, 1, 1),
            ],

            "Grave Titan": [
                ("Titan Bone", 0.6, 1, 1),
            ],

            "Nether Hound": [
                ("Nether Edge", 0.6, 1, 1),
            ],

            "Crystal Guardian": [

            ],

            "Void Reaper": [
                ("Void Crown", 0.6, 1, 1),
            ],

            "Ancient Lich": [

            ],

            "Frost Titan": [

            ],

            "Abyss Overlord": [
                ("Abyss Overlord Blade", 0.6, 1, 1),
                ("Overlord Sigil", 0.6, 1, 1),
            ],
        }

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
