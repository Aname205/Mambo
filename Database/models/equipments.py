class EquipmentsDB:
    def __init__(self, db):
        self.db = db

    async def create_table(self):
        async with self.db.cursor() as cursor:
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS equipments(
                    item_id INTEGER PRIMARY KEY,
                    equipment_type TEXT NOT NULL CHECK(equipment_type IN ('weapon', 'armor', 'accessory')),
                    damage INTEGER DEFAULT 0,
                    armor INTEGER DEFAULT 0,
                    break_force INTEGER DEFAULT 0,
                    tier TEXT DEFAULT 'common' CHECK(tier IN ('common', 'rare', 'epic', 'legendary')),
                    price INTEGER DEFAULT 0,
                    critical_chance REAL DEFAULT 0,
                    dodge_chance REAL DEFAULT 0,
                    FOREIGN KEY (item_id) REFERENCES items(id)
                )
            """)
        await self.db.commit()

    async def add_equipment(
            self,
            name,
            emoji,
            equipment_type,
            damage=0,
            armor=0,
            break_force=0,
            tier="common",
            price=0,
            critical_chance=0,
            dodge_chance=0
    ):
        async with self.db.cursor() as cursor:
            await cursor.execute("""
                INSERT INTO items(name, emoji, item_type)
                VALUES (?, ?, 'equipment')""", (name, emoji))

            item_id = cursor.lastrowid

            await cursor.execute("""
                INSERT INTO equipments(item_id, equipment_type, damage, armor,
                    break_force, tier, price, critical_chance, dodge_chance)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        item_id, equipment_type, damage, armor,
                        break_force, tier, price, critical_chance, dodge_chance
                    )
                )

        await self.db.commit()

    async def get_equipment(self, item_id):
        async with self.db.cursor() as cursor:
            await cursor.execute("""
                    SELECT * FROM equipments
                    INNER JOIN items ON items.id = equipments.item_id
                    WHERE equipments.item_id = ?""", (item_id,))

            equipment = await cursor.fetchone()

        return equipment

    async def get_equipment_by_type(self, equipment_type):
        async with self.db.cursor() as cursor:
            await cursor.execute("""
                SELECT * FROM equipments
                INNER JOIN items ON items.id = equipments.item_id
                WHERE equipment_type = ?
                """, (equipment_type,))

            items = await cursor.fetchall()

        return items

    async def get_equipment_by_tier(self, tier):
        async with self.db.cursor() as cursor:
            await cursor.execute("""
                SELECT * FROM equipments
                INNER JOIN items ON items.id = equipments.item_id
                WHERE tier = ?
                """, (tier,))

            items = await cursor.fetchall()

        return items