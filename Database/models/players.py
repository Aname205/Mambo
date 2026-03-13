class PlayersDB:
    def __init__(self, db):
        self.db = db

    async def create_table(self):
        async with self.db.cursor() as cursor:
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS players(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    
                    health INTEGER default 10,
                    damage INTEGER default 1,
                    armor INTEGER default 0,
                    speed INTEGER default 10,
                    break_force INTEGER default 0,
                    critical_chance REAL default 0.05,
                    dodge_chance REAL default 0.05,
                    
                    equipped_weapon_id INTEGER,
                    equipped_armor_id INTEGER,
                    equipped_accessory_1_id INTEGER,
                    equipped_accessory_2_id INTEGER,
                    level INTEGER default 1,
                    exp INTEGER default 0,
                    FOREIGN KEY (equipped_weapon_id) REFERENCES equipments(id),
                    FOREIGN KEY (equipped_armor_id) REFERENCES equipments(id),
                    FOREIGN KEY (equipped_accessory_1_id) REFERENCES equipments(id),
                    FOREIGN KEY (equipped_accessory_2_id) REFERENCES equipments(id)
                )
            """)
            await self.db.commit()

        await self._ensure_columns()

    async def _ensure_columns(self):
        """Ensure new columns exist for already-created DBs."""
        async with self.db.cursor() as cursor:
            await cursor.execute("PRAGMA table_info(players)")
            cols = [row[1] for row in await cursor.fetchall()]

            if "level" not in cols:
                await cursor.execute("ALTER TABLE players ADD COLUMN level INTEGER DEFAULT 1")
            if "exp" not in cols:
                await cursor.execute("ALTER TABLE players ADD COLUMN exp INTEGER DEFAULT 0")
        await self.db.commit()

    async def create_player(self, user_id):
        async with self.db.cursor() as cursor:
            await cursor.execute("""
                INSERT OR IGNORE INTO players(user_id) 
                VALUES(?)""", (user_id,))
        await self.db.commit()

    @staticmethod
    def exp_required(level):
        thresholds = [
            0, 120, 343, 669, 1097, 1629, 2263, 3000, 3840, 4783, 5829, 6977, 8229, 9583, 11040, 12600, 14263, 16029, 17897, 19869, 21943, 24120, 26400, 28783, 31269, 33857, 36549, 39343, 42240, 45240,
            50240, 55740, 61740, 68240, 75240, 82740, 90740, 99240, 108240, 117740, 127740, 138240, 149240, 160740, 172740, 185240, 198240, 211740, 225740, 240240
        ]
        if 1 <= level <= 50:
            return thresholds[level-1]
        return thresholds[-1]

    async def add_exp(self, user_id, amount):
        async with self.db.cursor() as cursor:
            await cursor.execute("SELECT level, exp FROM players WHERE user_id = ?", (user_id,))
            row = await cursor.fetchone()
            if not row:
                return False
            current_level, current_exp = row
            new_exp = current_exp + amount
            new_level = current_level
            while new_level < 50 and new_exp >= self.exp_required(new_level + 1):
                new_exp -= self.exp_required(new_level + 1)
                new_level += 1
            await cursor.execute("UPDATE players SET level = ?, exp = ? WHERE user_id = ?", (new_level, new_exp, user_id))
        await self.db.commit()
        return new_level > current_level

    async def get_player(self, user_id):
        async with self.db.cursor() as cursor:
            await cursor.execute("""
                SELECT * FROM players 
                WHERE user_id = ?""", (user_id,))
            player = await cursor.fetchone()

        if player is None:
            await self.create_player(user_id)
            return await self.get_player(user_id)

        return player

    # Flexible stat update
    async def update_stats(self, user_id, **kwargs):
        if not kwargs:
            return

        fields = []
        values = []

        for key, value in kwargs.items():
            fields.append(f"{key} = ?")
            values.append(value)

        values.append(user_id)

        query = f"""
            UPDATE players
            SET {', '.join(fields)}
            WHERE user_id = ?"""

        async with self.db.cursor() as cursor:
            await cursor.execute(query, tuple(values))

        await self.db.commit()

    async def recalculate_stats(self, user_id):
        async with self.db.cursor() as cursor:
            # Get base stats (assuming base stats are 10 health, 1 damage, 0 armor, 10 speed, 0 break_force, 0.05 crit, 0.05 dodge)
            base_health = 10
            base_damage = 1
            base_armor = 0
            base_speed = 10
            base_break_force = 0
            base_crit = 0.05
            base_dodge = 0.05
            
            # Get equipped items
            await cursor.execute("""
                SELECT equipped_weapon_id, equipped_armor_id, equipped_accessory_1_id, equipped_accessory_2_id
                FROM players
                WHERE user_id = ?
                """, (user_id,))
            
            equipped = await cursor.fetchone()
            if not equipped:
                return
            
            weapon_id, armor_id, acc1_id, acc2_id = equipped
            
            # Calculate total stats from equipment
            total_health = base_health
            total_damage = base_damage
            total_armor = base_armor
            total_speed = base_speed
            total_break_force = base_break_force
            total_crit = base_crit
            total_dodge = base_dodge
            
            # Add stats from each equipped item
            for eq_id in [weapon_id, armor_id, acc1_id, acc2_id]:
                if eq_id:
                    await cursor.execute("""
                        SELECT health, damage, armor, speed, break_force, critical_chance, dodge_chance
                        FROM equipments
                        WHERE id = ?
                        """, (eq_id,))
                    
                    eq_stats = await cursor.fetchone()
                    if eq_stats:
                        total_health += eq_stats[0]
                        total_damage += eq_stats[1]
                        total_armor += eq_stats[2]
                        total_speed += eq_stats[3]
                        total_break_force += eq_stats[4]
                        total_crit += eq_stats[5]
                        total_dodge += eq_stats[6]
            
            # Update player stats
            await cursor.execute("""
                UPDATE players
                SET health = ?,
                    damage = ?,
                    armor = ?,
                    speed = ?,
                    break_force = ?,
                    critical_chance = ?,
                    dodge_chance = ?
                WHERE user_id = ?
                """, (total_health, total_damage, total_armor, total_speed, total_break_force, total_crit, total_dodge, user_id))
        
        await self.db.commit()

    # Equip weapon or armor
    async def equip_item(self, user_id, inv_id, slot):

        async with self.db.cursor() as cursor:

            # Get item_id and tier from inventory
            await cursor.execute("""
                SELECT item_id, item_tier
                FROM inventories
                WHERE id = ?
                AND user_id = ?
                """, (inv_id, user_id))

            row = await cursor.fetchone()

            if not row:
                return

            item_id, item_tier = row
            
            # Get equipment_id from equipments table
            await cursor.execute("""
                SELECT id
                FROM equipments
                WHERE item_id = ?
                AND tier = ?
                """, (item_id, item_tier))
            
            eq_row = await cursor.fetchone()
            
            if not eq_row:
                return
                
            equipment_id = eq_row[0]

            # Determine column and get old equipment
            old_equipment = None
            column = None
            
            if slot == "weapon":
                column = "equipped_weapon_id"
                await cursor.execute("""
                    SELECT equipped_weapon_id
                    FROM players
                    WHERE user_id = ?
                    """, (user_id,))
                old_equipment = (await cursor.fetchone())[0]

            elif slot == "armor":
                column = "equipped_armor_id"
                await cursor.execute("""
                    SELECT equipped_armor_id
                    FROM players
                    WHERE user_id = ?
                    """, (user_id,))
                old_equipment = (await cursor.fetchone())[0]

            elif slot == "accessory_1":
                column = "equipped_accessory_1_id"
                await cursor.execute("""
                    SELECT equipped_accessory_1_id
                    FROM players
                    WHERE user_id = ?
                    """, (user_id,))
                old_equipment = (await cursor.fetchone())[0]
                
            elif slot == "accessory_2":
                column = "equipped_accessory_2_id"
                await cursor.execute("""
                    SELECT equipped_accessory_2_id
                    FROM players
                    WHERE user_id = ?
                    """, (user_id,))
                old_equipment = (await cursor.fetchone())[0]
                
            elif slot == "accessory":
                # Legacy "accessory" slot - auto-assign to first available
                await cursor.execute("""
                    SELECT equipped_accessory_1_id, equipped_accessory_2_id
                    FROM players
                    WHERE user_id = ?
                    """, (user_id,))

                acc1, acc2 = await cursor.fetchone()

                if acc1 is None:
                    column = "equipped_accessory_1_id"
                    old_equipment = None
                else:
                    column = "equipped_accessory_2_id"
                    old_equipment = acc2
            else:
                # Invalid slot
                return
            
            if column is None:
                return

            # Return old equipment to inventory
            if old_equipment:
                # Get item_id and tier from equipment_id
                await cursor.execute("""
                    SELECT item_id, tier
                    FROM equipments
                    WHERE id = ?
                    """, (old_equipment,))
                
                old_eq_row = await cursor.fetchone()
                
                if old_eq_row:
                    old_item_id, old_tier = old_eq_row
                    await cursor.execute("""
                        INSERT INTO inventories(user_id, item_id, item_tier)
                        VALUES (?, ?, ?)
                        """, (user_id, old_item_id, old_tier))

            # Remove new equipment from inventory
            await cursor.execute("""
                DELETE
                FROM inventories
                WHERE id = ?
                """, (inv_id,))

            # Equip item
            await cursor.execute(f"""
                UPDATE players
                SET {column} = ?
                WHERE user_id = ?
            """, (equipment_id, user_id))

        await self.db.commit()
        
        # Recalculate player stats based on new equipment
        await self.recalculate_stats(user_id)

    async def get_equipped_items(self, user_id):
        """Get all equipped items with their full details"""
        async with self.db.cursor() as cursor:
            await cursor.execute("""
                SELECT 
                    p.equipped_weapon_id,
                    p.equipped_armor_id,
                    p.equipped_accessory_1_id,
                    p.equipped_accessory_2_id
                FROM players p
                WHERE p.user_id = ?
                """, (user_id,))
            
            equipped_ids = await cursor.fetchone()
            
            if not equipped_ids:
                return None, None, None, None
            
            weapon_id, armor_id, acc1_id, acc2_id = equipped_ids
            
            # Helper function to get equipment details
            async def get_equipment_details(eq_id):
                if not eq_id:
                    return None
                
                await cursor.execute("""
                    SELECT 
                        e.id,
                        i.id,
                        i.name,
                        i.emoji,
                        e.tier,
                        0 as price,
                        0 as market_price,
                        0 as is_lock,
                        e.equipment_type,
                        e.health,
                        e.damage,
                        e.armor,
                        e.speed,
                        e.break_force,
                        e.critical_chance,
                        e.dodge_chance
                    FROM equipments e
                    JOIN items i ON e.item_id = i.id
                    WHERE e.id = ?
                    """, (eq_id,))
                
                return await cursor.fetchone()
            
            weapon = await get_equipment_details(weapon_id)
            armor = await get_equipment_details(armor_id)
            acc1 = await get_equipment_details(acc1_id)
            acc2 = await get_equipment_details(acc2_id)
            
            return weapon, armor, acc1, acc2