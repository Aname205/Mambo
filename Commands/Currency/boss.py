import discord
from discord.ext import commands
import asyncio
import random

TURN_DELAY = 1


def calculate_scaled_damage(attack, defense):
    """Common mitigation formula: atk * (100 / (100 + def))."""
    denom = 100 + max(0, defense)
    return max(0.0, attack * (100 / denom))


class Boss(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def run_boss_battle(self, ctx, battle_id):

        # Use the same DB call as hunt.py
        battle = await self.bot.db.get_active_battle(battle_id)
        if not battle:
            return

        player_id = battle[1]

        p_hp     = battle[3]
        p_damage = battle[4]
        p_armor  = battle[5]
        p_speed  = battle[6]
        p_break  = battle[7]
        p_crit   = battle[8]
        p_dodge  = battle[9]

        m_hp       = battle[10]
        m_damage   = battle[11]
        m_armor    = battle[12]
        m_tenacity = battle[13]
        m_speed    = battle[14]
        m_crit     = battle[15]
        m_dodge    = battle[16]

        m_level      = battle[17]
        m_currency   = battle[18]
        m_exp_min    = battle[19]
        m_exp_max    = battle[20]
        m_modifier   = battle[21]
        loot_table_id = battle[22]

        # Fetch the monster's base level for loot tier scaling (same as hunt.py)
        monster_id = battle[2]
        raw_monster = await self.bot.db.get_monster(monster_id)
        m_base_level = raw_monster[9] if raw_monster else 1

        max_tenacity = m_tenacity
        is_stunned = False

        # Same gauge logic as hunt.py
        max_gauge = max(p_speed, m_speed)
        p_gauge = 0
        m_gauge = 0

        battle_log = []

        # Same initial message style as hunt.py
        message = await ctx.send("⚔️ **Boss Battle Started**")

        while p_hp > 0 and m_hp > 0:

            if p_gauge < max_gauge and m_gauge < max_gauge:
                p_gauge += p_speed
                m_gauge += m_speed
                continue

            actor = None

            if p_gauge >= max_gauge and m_gauge >= max_gauge:
                actor = 1 if p_gauge >= m_gauge else 2
            elif p_gauge >= max_gauge:
                actor = 1
            elif m_gauge >= max_gauge:
                actor = 2

            # PLAYER TURN
            if actor == 1:
                p_gauge -= max_gauge

                if random.random() < m_dodge and not is_stunned:
                    battle_log.append("👹 Boss **dodged** your attack")
                else:
                    base_damage = calculate_scaled_damage(p_damage, m_armor)
                    damage = int(base_damage * random.uniform(0.8, 1.2))

                    if is_stunned:
                        damage *= 2
                        is_stunned = False
                        m_tenacity = max_tenacity
                        battle_log.append("💫 Stunned Boss took double damage!")

                    if random.random() < p_crit:
                        damage *= 2
                        crit = "💥 **CRIT**"
                    else:
                        crit = ""

                    m_hp -= damage

                    battle_log.append(
                        f"{ctx.author.mention} hits Boss for **{damage}** {crit}"
                    )

                    if not is_stunned and max_tenacity > 0:
                        m_tenacity -= p_break
                        if m_tenacity <= 0:
                            is_stunned = True
                            m_tenacity = 0
                            battle_log.append("💫 Boss's tenacity broke! It is **Stunned**!")

                await asyncio.sleep(TURN_DELAY)

            # BOSS TURN
            if actor == 2:
                m_gauge -= max_gauge

                if is_stunned:
                    battle_log.append("💫 Boss is **Stunned** and skips its turn!")
                else:
                    if random.random() < p_dodge:
                        battle_log.append("👟 You **dodged** the Boss attack")
                    else:
                        base_damage = calculate_scaled_damage(m_damage, p_armor)
                        damage = int(base_damage * random.uniform(0.8, 1.2))

                        if random.random() < m_crit:
                            damage *= 2
                            crit = "💥 **CRIT**"
                        else:
                            crit = ""

                        p_hp -= damage
                        battle_log.append(f"👹 Boss hits you for **{damage}** {crit}")

                await asyncio.sleep(TURN_DELAY)

            # Build embed — same structure as hunt.py
            embed = discord.Embed(
                title="⚔️ Boss Battle",
                description="\n".join(battle_log[-6:]),
                color=discord.Color.dark_red()
            )

            player_stats = (
                f"❤️ HP: **{p_hp}**\n"
                f"⚔️ Damage: **{p_damage}**\n"
                f"🛡️ Armor: **{p_armor}**\n"
                f"💨 Speed: **{p_speed}**\n"
                f"⚡ Break: **{p_break}**\n"
                f"🎯 Crit: **{p_crit * 100:.1f}%**\n"
                f"👟 Dodge: **{p_dodge * 100:.1f}%**"
            )

            monster_stats = (
                f"❤️ HP: **{m_hp}**\n"
                f"⚔️ Damage: **{m_damage}**\n"
                f"🛡️ Armor: **{m_armor}**\n"
                f"💨 Speed: **{m_speed}**\n"
                f"🧱 Tenacity: **{m_tenacity}**\n"
                f"🎯 Crit: **{m_crit * 100:.1f}%**\n"
                f"👟 Dodge: **{m_dodge * 100:.1f}%**\n"
                f"🎖 Level: **{m_level}**\n"
            )

            embed.add_field(
                name=f"🧑 {ctx.author.display_name}",
                value=player_stats,
                inline=True
            )
            embed.add_field(
                name=f"👹 Boss ({m_modifier})",
                value=monster_stats,
                inline=True
            )

            await message.edit(embed=embed)

            if p_hp <= 0 or m_hp <= 0:
                break

        # ===== PLAYER LOST =====
        if p_hp <= 0:
            await self.bot.db.battle_logs.end_battle(battle_id, "lost")
            battle_log.append("💀 You were defeated by the Boss!")

        # ===== PLAYER WON =====
        else:
            await self.bot.db.battle_logs.end_battle(battle_id, "won")
            battle_log.append("🏆 You defeated the Boss!")

            # Advance boss level — use COALESCE so NULL+1 doesn't silently stay NULL
            async with self.bot.db.db.cursor() as cursor:
                await cursor.execute(
                    "UPDATE players SET boss_level = COALESCE(boss_level, 1) + 1 WHERE user_id = ?",
                    (player_id,)
                )
            await self.bot.db.db.commit()
            battle_log.append("⭐ **You've advanced to the next Boss level!**")

            # Award EXP — same as hunt.py
            exp_gained = random.randint(m_exp_min, m_exp_max)

            player_data_before = await self.bot.db.get_player(player_id)
            level_before = player_data_before[13]

            leveled_up = await self.bot.db.add_exp(player_id, exp_gained)

            player_data = await self.bot.db.get_player(player_id)
            current_level = player_data[13]
            current_exp   = player_data[14]
            exp_needed = self.bot.db.players.exp_required(current_level + 1)

            if leveled_up:
                levels_gained = current_level - level_before
                health_gain = levels_gained * 10
                damage_gain = levels_gained * 2
                armor_gain  = sum(1 for lvl in range(level_before + 1, current_level + 1) if lvl % 2 == 0)
                speed_gain  = sum(1 for lvl in range(level_before + 1, current_level + 1) if lvl % 5 == 0)
                ap_gain = levels_gained * 3

                stat_text = f"❤️ +{health_gain} HP | ⚔️ +{damage_gain} DMG"
                if armor_gain > 0:
                    stat_text += f" | 🛡️ +{armor_gain} ARM"
                if speed_gain > 0:
                    stat_text += f" | 💨 +{speed_gain} SPD"
                stat_text += f"\n💎 +{ap_gain} Ability Points"

                battle_log.append(
                    f"**-----------------------------------\n"
                    f"⭐ LEVEL UP! You are now level {current_level}!\n"
                    f"{stat_text}\n"
                    f"-----------------------------------**"
                )
            else:
                battle_log.append(
                    f"**-----------------------------------\n"
                    f"✨ You gained {exp_gained} EXP ({current_exp}/{exp_needed})\n"
                    f"-----------------------------------**"
                )

            # Roll loot — same as hunt.py
            drops = await self.bot.db.roll_loot(loot_table_id, m_modifier, m_level, m_base_level)

            if drops or m_currency > 0:
                battle_log.append("🎁 **Drops:**")

                if m_currency > 0:
                    await self.bot.db.update_wallet(player_id, m_currency)
                    battle_log.append(f"💰 {m_currency} 🪙")

                for drop in drops:
                    item_id = drop["item_id"]
                    tier    = drop["tier"]
                    amount  = drop["amount"]
                    name    = drop["name"]
                    emoji   = drop["emoji"]

                    await self.bot.db.add_to_inventory(player_id, item_id, tier, amount)

                    tier_str = f"[{tier}] " if tier else ""
                    battle_log.append(f"{emoji} {tier_str}{name} x{amount}")
            else:
                battle_log.append("😢 No items dropped")

        # Final result embed — same as hunt.py
        embed = discord.Embed(
            title="⚔️ Boss Battle Finished",
            description="\n".join(battle_log[-10:]),
            color=discord.Color.gold()
        )
        embed.add_field(name="Player HP", value=f"{ctx.author.mention} ❤️ {max(0, p_hp)}")
        embed.add_field(name="Boss HP",   value=f"👹 ❤️ {max(0, m_hp)}")
        await message.edit(embed=embed)

    @commands.command()
    async def boss(self, ctx):
        try:
            player = await self.bot.db.players.get_player(ctx.author.id)

            # boss_level may be NULL for players created before the column migration
            boss_level = player[23] if player[23] is not None else 1

            # Persist default if NULL
            if player[23] is None:
                async with self.bot.db.db.cursor() as cursor:
                    await cursor.execute(
                        "UPDATE players SET boss_level = 1 WHERE user_id = ?",
                        (ctx.author.id,)
                    )
                await self.bot.db.db.commit()

            # Boss progression table
            boss_name = None
            if boss_level == 1:
                boss_name = "Normal Arthropleura"
            elif boss_level == 2:
                boss_name = "Normal Yeti"

            if boss_name is None:
                return await ctx.send("🎉 You have defeated all current bosses! Wait for the next update.")

            boss_record = await self.bot.db.monsters.get_monster_by_name(boss_name)

            if not boss_record:
                return await ctx.send(f"⚠️ Error: Boss **{boss_name}** could not be found in the database.")

            monster = boss_record

            battle_id = await self.bot.db.battle_logs.start_battle(
                ctx.author.id,
                monster[0],   # monster_id
                player[2],    # p_health
                player[3],    # p_damage
                player[4],    # p_armor
                player[5],    # p_speed
                player[6],    # p_break
                player[7],    # p_crit
                player[8],    # p_dodge
                monster[2],   # m_health
                monster[3],   # m_damage
                monster[4],   # m_armor
                monster[5],   # m_tenacity
                monster[6],   # m_speed
                monster[7],   # m_crit
                monster[8],   # m_dodge
                monster[9],   # m_level
                monster[10],  # m_currency
                monster[11],  # m_exp_min
                monster[12],  # m_exp_max
                monster[13],  # m_modifier
                monster[14]   # m_loot_table_id
            )

            await ctx.send(f"👹 A **{monster[1]}** (Lv.**{monster[9]}**) appeared!")

            asyncio.create_task(self.run_boss_battle(ctx, battle_id))

        except Exception as e:
            return await ctx.send(f"Error: {e}")

    @commands.command(name="bossreset")
    async def bossreset(self, ctx):
        """Reset your boss progression back to level 1 (Boss 1: Arthropleura)."""
        try:
            async with self.bot.db.db.cursor() as cursor:
                await cursor.execute(
                    "UPDATE players SET boss_level = 1 WHERE user_id = ?",
                    (ctx.author.id,)
                )
            await self.bot.db.db.commit()
            await ctx.send("🔄 Your boss progression has been reset! You will now face **Normal Arthropleura** again.")
        except Exception as e:
            await ctx.send(f"Error: {e}")


async def setup(bot):
    await bot.add_cog(Boss(bot))
