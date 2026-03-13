"""
One-time migration script to populate AP tracking columns for existing players.
Run this once after adding the AP tracking feature.
"""
import asyncio
import aiosqlite

async def migrate_ap_tracking():
    db = await aiosqlite.connect('database.db')
    
    async with db.cursor() as cursor:
        # Get all players
        await cursor.execute("SELECT user_id, level, health, damage, armor, speed, break_force, critical_chance, dodge_chance FROM players")
        players = await cursor.fetchall()
        
        for player in players:
            user_id, level, health, damage, armor, speed, break_force, crit, dodge = player
            
            # Calculate base stats from level
            base_health = 20 + (level - 1) * 10
            base_damage = 5 + (level - 1) * 2
            base_armor = 0 + (level - 1) * 1
            base_speed = 10 + ((level - 1) // 5)
            base_break_force = 1
            base_crit = 0.05
            base_dodge = 0.05
            
            # Calculate AP spent (accounting for equipment bonuses being included)
            # This is a best-effort calculation
            ap_health = max(0, int((health - base_health) / 5))
            ap_damage = max(0, int(damage - base_damage))
            ap_armor = max(0, int((armor - base_armor) / 0.5))
            ap_speed = max(0, int(round((speed - base_speed) / 0.2)))
            ap_break = max(0, int(round((break_force - base_break_force) / 0.2)))
            ap_crit = max(0, int(round((crit - base_crit) / 0.003)))
            ap_dodge = max(0, int(round((dodge - base_dodge) / 0.001)))
            
            # Update AP tracking columns
            await cursor.execute("""
                UPDATE players
                SET ap_health = ?,
                    ap_damage = ?,
                    ap_armor = ?,
                    ap_speed = ?,
                    ap_break = ?,
                    ap_crit = ?,
                    ap_dodge = ?
                WHERE user_id = ?
            """, (ap_health, ap_damage, ap_armor, ap_speed, ap_break, ap_crit, ap_dodge, user_id))
            
            print(f"Migrated user {user_id}: HP+{ap_health}, DMG+{ap_damage}, ARM+{ap_armor}, SPD+{ap_speed}, BRK+{ap_break}, CRIT+{ap_crit}, DODGE+{ap_dodge}")
    
    await db.commit()
    await db.close()
    print("\nMigration complete!")

if __name__ == "__main__":
    asyncio.run(migrate_ap_tracking())
