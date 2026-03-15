class ItemPassivesDB:
    def __init__(self, db):
        self.db = db

    async def create_table(self):
        async with self.db.cursor() as cursor:
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS item_passives(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    inventory_id INTEGER NOT NULL,
                    passive_id INTEGER NOT NULL,
                    FOREIGN KEY (inventory_id) REFERENCES inventories(id) ON DELETE CASCADE,
                    FOREIGN KEY (passive_id) REFERENCES passives(id) ON DELETE CASCADE
                )
            """)
        await self.db.commit()

    async def add_item_passive(self, inventory_id, passive_id):
        async with self.db.cursor() as cursor:
            await cursor.execute("""
                INSERT INTO item_passives(inventory_id, passive_id)
                VALUES (?, ?)
            """, (inventory_id, passive_id))
            await self.db.commit()
            return cursor.lastrowid

    async def get_passives_for_item(self, inventory_id):
        # Returns: (item_passive_id, passive_id, effect, emoji, affix_suffix, equipment_type)
        async with self.db.cursor() as cursor:
            await cursor.execute("""
                SELECT ip.id, p.id, p.effect, p.emoji, p.affix_suffix, p.equipment_type
                FROM item_passives ip
                JOIN passives p ON ip.passive_id = p.id
                WHERE ip.inventory_id = ?
            """, (inventory_id,))
            return await cursor.fetchall()

    async def get_passives_for_equipped_weapon(self, user_id):
        """Get passives for the currently equipped weapon by looking up is_equipped inventory row."""
        # Returns: list of effect names
        async with self.db.cursor() as cursor:
            await cursor.execute("""
                SELECT ip.id, p.id, p.effect, p.emoji, p.affix_suffix, p.equipment_type
                FROM item_passives ip
                JOIN passives p ON ip.passive_id = p.id
                JOIN inventories inv ON ip.inventory_id = inv.id
                JOIN items i ON inv.item_id = i.id
                JOIN equipments e ON e.item_id = i.id AND e.tier = inv.item_tier
                JOIN players pl ON pl.equipped_weapon_id = e.id
                WHERE pl.user_id = ? AND inv.is_equipped = 1
            """, (user_id,))
            return await cursor.fetchall()

    async def remove_item_passive(self, item_passive_id):
        async with self.db.cursor() as cursor:
            await cursor.execute("DELETE FROM item_passives WHERE id = ?", (item_passive_id,))
        await self.db.commit()

    async def remove_all_passives_for_item(self, inventory_id):
        async with self.db.cursor() as cursor:
            await cursor.execute(
                "DELETE FROM item_passives WHERE inventory_id = ?", (inventory_id,)
            )
        await self.db.commit()
