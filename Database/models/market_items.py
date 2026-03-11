class MarketItemsDB:
    def __init__(self, db):
        self.db = db

    async def create_table(self):
        async with self.db.cursor() as cursor:
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS market_items(
                id INTEGER PRIMARY KEY,
                price INTEGER,
                tier TEXT,
                description TEXT,
                FOREIGN KEY (id) REFERENCES items(id)
                )
            """)
        await self.db.commit()

    async def get_market_equipments(self):
        async with self.db.cursor() as cursor:
            await cursor.execute("""
                SELECT 
                    equipments.item_id,
                    items.name,
                    items.emoji,
                    equipments.equipment_type,
                    equipments.health,
                    equipments.damage,
                    equipments.armor,
                    equipments.speed,
                    equipments.break_force,
                    equipments.tier,
                    equipments.price AS price,
                    equipments.critical_chance,
                    equipments.dodge_chance
                FROM equipments
                    JOIN items ON items.id = equipments.item_id
                    WHERE equipments.market_only = 1
                    ORDER BY equipments.price
            """)
            return await cursor.fetchall()
