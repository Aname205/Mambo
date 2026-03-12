class InventoriesDB:
    def __init__(self, db):
        self.db = db

    async def create_table(self):
        async with self.db.cursor() as cursor:
            await cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventories(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            item_id INTEGER,
            item_tier TEXT,
            amount INTEGER DEFAULT 1,
            is_lock BOOLEAN DEFAULT 0,
            FOREIGN KEY (item_id) REFERENCES items(id)
        )
        """)
        await self.db.commit()

    async def get_inventory(self, user_id):
        async with self.db.cursor() as cursor:
            await cursor.execute("""
                SELECT 
                    inv.id, 
                    i.id, 
                    i.name, 
                    i.emoji, 
                    inv.item_tier,
                    inv.amount,
                    fi.price,
                    COALESCE(em.price, mi.price) AS market_price,
                    inv.is_lock,
                    em.equipment_type,
                    em.health,
                    em.damage,
                    em.armor,
                    em.speed,
                    em.break_force,
                    em.critical_chance,
                    em.dodge_chance
                FROM inventories inv
                    JOIN items i ON inv.item_id = i.id
                    LEFT JOIN fishing_items fi 
                        ON i.id = fi.item_id AND fi.tier = inv.item_tier
                    LEFT JOIN market_items mi 
                        ON i.id = mi.id AND mi.tier = inv.item_tier
                    LEFT JOIN equipments em
                        ON i.id = em.item_id AND em.tier = inv.item_tier
                WHERE inv.user_id = ? """, (user_id,)
            )
            return await cursor.fetchall()

    async def add_to_inventory(self, user_id, item_id, item_tier, amount):
        stackable = await self.get_item_stackable(item_id)

        async with self.db.cursor() as cursor:

            if stackable:
                # stack items
                await cursor.execute("""
                     SELECT amount
                     FROM inventories
                     WHERE user_id = ?
                       AND item_id = ?
                       AND item_tier = ?
                     """, (user_id, item_id, item_tier))

                row = await cursor.fetchone()

                if row:
                    await cursor.execute("""
                         UPDATE inventories
                         SET amount = amount + ?
                         WHERE user_id = ?
                           AND item_id = ?
                           AND item_tier = ?
                         """, (amount, user_id, item_id, item_tier))

                else:
                    await cursor.execute("""
                         INSERT INTO inventories(user_id, item_id, item_tier, amount)
                         VALUES (?, ?, ?, ?)
                         """, (user_id, item_id, item_tier, amount))

            else:
                # non-stackable (equipment)
                for _ in range(amount):
                    await cursor.execute("""
                         INSERT INTO inventories(user_id, item_id, item_tier, amount)
                         VALUES (?, ?, ?, 1)
                         """, (user_id, item_id, item_tier))
        await self.db.commit()

    async def remove_from_inventory(self, user_id, item_id, item_tier, amount):
        stackable = await self.get_item_stackable(item_id)

        async with self.db.cursor() as cursor:

            if stackable:
                await cursor.execute("""
                     UPDATE inventories
                     SET amount = amount - ?
                     WHERE user_id = ?
                       AND item_id = ?
                       AND item_tier = ?
                     """, (amount, user_id, item_id, item_tier))

                await cursor.execute("""
                     DELETE
                     FROM inventories
                     WHERE user_id = ?
                       AND item_id = ?
                       AND item_tier = ?
                       AND amount <= 0
                     """, (user_id, item_id, item_tier))

            else:
                await cursor.execute("""
                     DELETE
                     FROM inventories
                     WHERE id IN (SELECT id
                          FROM inventories
                          WHERE user_id = ?
                            AND item_id = ?
                            AND item_tier = ?
                         LIMIT ?
                         )
                     """, (user_id, item_id, item_tier, amount))

        await self.db.commit()

    async def remove_all_from_inventory(self, user_id):
        async with self.db.cursor() as cursor:
            await cursor.execute(""" 
                DELETE FROM inventories 
                WHERE user_id = ? 
                AND is_lock = 0""", (user_id,)
            )
            await self.db.commit()

    async def set_item_lock(self, item_id, is_locked):
        async with self.db.cursor() as cursor:
            await cursor.execute(
                "UPDATE inventories SET is_lock = ? WHERE id = ?",
                (1 if is_locked else 0, item_id)
            )
        await self.db.commit()

    async def get_item_stackable(self, item_id):
        async with self.db.cursor() as cursor:
            await cursor.execute(
                "SELECT item_type FROM items WHERE id = ?",
                (item_id,)
            )

            row = await cursor.fetchone()

            if not row:
                return True

            item_type = row[0]

            return item_type not in ("equipment")