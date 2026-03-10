class EquipmentsDB:
    def __init__(self, db):
        self.db = db

    async def create_table(self):
        async with self.db.cursor() as cursor:
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS equipments(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_id INTEGER,
                    equipment_type TEXT NOT NULL CHECK(equipment_type IN ('weapon', 'armor', 'accessory')),
                    damage INTEGER DEFAULT 0,
                    armor INTEGER DEFAULT 0,
                    break_force INTEGER DEFAULT 0,
                    tier TEXT DEFAULT 'common' CHECK(tier IN ('common','uncommon','rare','epic','legendary')),
                    price INTEGER DEFAULT 0,
                    critical_chance REAL DEFAULT 0,
                    dodge_chance REAL DEFAULT 0,
                    UNIQUE(item_id, tier),
                    FOREIGN KEY (item_id) REFERENCES items(id)
                )
            """)
        await self.db.commit()

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
        async with self.db.cursor() as cursor:
            await cursor.execute("""
                INSERT OR REPLACE INTO equipments(
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
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
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
                )
        await self.db.commit()

    async def get_equipment(self, item_id):
        async with self.db.cursor() as cursor:
            await cursor.execute("""
                    SELECT * FROM equipments
                    INNER JOIN items ON items.id = equipments.item_id
                    WHERE equipments.item_id = ?""", (item_id,))

            equipment = await cursor.fetchall()

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

    async def generate_equipments(self, items_db):
        try:
            base_equipments = [
                ("Stick", "🏑", "weapon",  1, 0, 1, 20, 0, 0),
                ("Rag", "👕", "armor", 0, 1, 0, 20, 0, 0),
                ("Wooden Sword", "🗡️", "weapon", 3, 0 , 1, 50, 0.01, 0)
            ]

            TIERS = {
                "common": {
                    "damage_mult": 1,
                    "armor_mult": 1,
                    "break_force_mult": 1,
                    "price_mult": 1,
                    "critical_chance_mult": 1,
                    "dodge_chance_mult": 1
                },

                "uncommon": {
                    "damage_mult": 1.1,
                    "armor_mult": 1.05,
                    "break_force_mult": 1.1,
                    "price_mult": 1.1,
                    "critical_chance_mult": 1,
                    "dodge_chance_mult": 1
                },

                "rare": {
                    "damage_mult": 1.2,
                    "armor_mult": 1.1,
                    "break_force_mult": 1.2,
                    "price_mult": 1.15,
                    "critical_chance_mult": 1.05,
                    "dodge_chance_mult": 1.05
                },

                "epic": {
                    "damage_mult": 1.35,
                    "armor_mult": 1.2,
                    "break_force_mult": 1.3,
                    "price_mult": 1.25,
                    "critical_chance_mult": 1.1,
                    "dodge_chance_mult": 1.1
                },

                "legendary": {
                    "damage_mult": 1.5,
                    "armor_mult": 1.4,
                    "break_force_mult": 1.5,
                    "price_mult": 1.4,
                    "critical_chance_mult": 1.2,
                    "dodge_chance_mult": 1.2
                }
            }

            valid_keys = []

            for (name, emoji, equipment_type, base_damage, base_armor, base_break_force, base_price,
                base_critical_chance, base_dodge_chance) in base_equipments:

                item_id = await items_db.get_or_create_item(name, emoji, "equipment")

                for tier, mult in TIERS.items():
                    damage = int(base_damage * mult["damage_mult"])
                    armor = int(base_armor * mult["armor_mult"])
                    break_force = int(base_break_force * mult["break_force_mult"])
                    price = int(base_price * mult["price_mult"])
                    critical_chance = float(base_critical_chance * mult["critical_chance_mult"])
                    dodge_chance = float(base_dodge_chance * mult["dodge_chance_mult"])

                    await self.add_equipment(
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

                    valid_keys.append((item_id, tier))

            # Remove rows not in pool anymore
            async with self.db.cursor() as cursor:

                if valid_keys:
                    placeholders = ",".join(["(?, ?)"] * len(valid_keys))

                    values = [v for pair in valid_keys for v in pair]

                    await cursor.execute(f"""
                        DELETE FROM equipments
                        WHERE (item_id, tier) NOT IN ({placeholders})
                    """, values)
            await self.db.commit()

            # Remove equipments not in base pool
            valid_names = [equipment[0] for equipment in base_equipments]

            if valid_names:

                async with self.db.cursor() as cursor:

                    placeholders = ",".join("?" * len(valid_names))

                    await cursor.execute(f"""
                        DELETE FROM items
                        WHERE item_type='equipment'
                        AND name NOT IN ({placeholders})
                    """, valid_names)

                await self.db.commit()
        except Exception as e:
            print(f"Error generating equipments: {e}")
            raise

    async def ensure_equipments(self, items_db):
        await self.generate_equipments(items_db)