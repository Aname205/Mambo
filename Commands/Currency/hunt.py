import discord
from discord.ext import commands
import asyncio
import random

TURN_DELAY = 1

class Hunt(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def run_monster_battle(self, ctx, battle_id):

        battle = await self.bot.db.get_active_battle(battle_id)

        player_id = battle[1]

        p_hp = battle[3]
        p_damage = battle[4]
        p_armor = battle[5]
        p_speed = battle[6]
        p_break = battle[7]
        p_crit = battle[8]
        p_dodge = battle[9]

        m_hp = battle[10]
        m_damage = battle[11]
        m_armor = battle[12]
        m_tenacity = battle[13]
        m_speed = battle[14]
        m_crit = battle[15]
        m_dodge = battle[16]

        m_level = battle[17]
        m_currency = battle[18]
        m_modifier = battle[19]
        loot_table_id = battle[20]

        max_tenacity = m_tenacity
        is_stunned = False

        max_gauge = max(p_speed, m_speed)

        p_gauge = 0
        m_gauge = 0

        battle_log = []

        message = await ctx.send("⚔️ **Monster Battle Started**")

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
                    battle_log.append("👹 Monster **dodged** your attack")
                else:

                    base_damage = p_damage - m_armor
                    base_damage = max(base_damage, 0)

                    damage = int(base_damage * random.uniform(0.8, 1.2))

                    if is_stunned:
                        damage *= 2
                        is_stunned = False
                        m_tenacity = max_tenacity
                        battle_log.append("💫 Stunned monster took double damage!")

                    if random.random() < p_crit:
                        damage *= 2
                        crit = "💥 **CRIT**"
                    else:
                        crit = ""

                    m_hp -= damage

                    battle_log.append(
                        f"{ctx.author.mention} hits monster for **{damage}** {crit}"
                    )

                    if not is_stunned and max_tenacity > 0:
                        m_tenacity -= p_break
                        if m_tenacity <= 0:
                            is_stunned = True
                            m_tenacity = 0
                            battle_log.append("💫 Monster's tenacity broke! It is **Stunned**!")

                await asyncio.sleep(TURN_DELAY)

            # MONSTER TURN
            if actor == 2:

                m_gauge -= max_gauge

                if is_stunned:
                    battle_log.append("💫 Monster is **Stunned** and skips its turn!")
                else:
                    if random.random() < p_dodge:
                        battle_log.append("💨 You **dodged** the monster attack")
                    else:

                        base_damage = m_damage - p_armor
                        base_damage = max(base_damage, 0)

                        damage = int(base_damage * random.uniform(0.8, 1.2))

                        if random.random() < m_crit:
                            damage *= 2
                            crit = "💥 **CRIT**"
                        else:
                            crit = ""

                        p_hp -= damage

                        battle_log.append(
                            f"👹 Monster hits you for **{damage}** {crit}"
                        )

                await asyncio.sleep(TURN_DELAY)

            embed = discord.Embed(
                title="⚔️ Monster Battle",
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
                name=f"👹 Monster ({m_modifier})",
                value=monster_stats,
                inline=True
            )

            await message.edit(embed=embed)

            if p_hp <= 0 or m_hp <= 0:
                break

        # ===== PLAYER LOST =====
        if p_hp <= 0:

            await self.bot.db.battle_logs.end_battle(battle_id, "lost")

            battle_log.append("💀 You were defeated!")

        # ===== PLAYER WON =====
        else:

            await self.bot.db.battle_logs.end_battle(battle_id, "won")

            battle_log.append("🏆 You defeated the monster")

            # Currency reward
            await self.bot.db.update_wallet(player_id, m_currency)

            battle_log.append(f"**-----------------------------------\n💰 You gained {m_currency} 🪙\n----------------------------------**")

            # Roll loot
            drops = await self.bot.db.roll_loot(loot_table_id, m_modifier)

            if drops:

                battle_log.append("🎁 **Drops:**")

                for drop in drops:

                    item_id = drop["item_id"]
                    tier = drop["tier"]
                    amount = drop["amount"]
                    name = drop["name"]
                    emoji = drop["emoji"]

                    await self.bot.db.add_to_inventory(
                        player_id,
                        item_id,
                        tier,
                        amount
                    )

                    tier_str = f"[{tier}] " if tier else ""
                    battle_log.append(
                        f"{emoji} {tier_str}{name} x{amount}"
                    )

            else:
                battle_log.append("😢 No items dropped")

        embed = discord.Embed(
            title="⚔️ Battle Finished",
            description="\n".join(battle_log[-10:]),
            color=discord.Color.gold()
        )

        embed.add_field(name="Player HP", value=f"{ctx.author.mention} ❤️ {max(0,p_hp)}")
        embed.add_field(name="Monster HP", value=f"👹 ❤️ {max(0,m_hp)}")

        await message.edit(embed=embed)

    @commands.command()
    async def hunt(self, ctx):
        try:
            player = await self.bot.db.players.get_player(ctx.author.id)

            monster = await self.bot.db.monsters.get_random_monster()

            battle_id = await self.bot.db.battle_logs.start_battle(
                ctx.author.id,
                monster[0],  # monster_id
                player[2],  # p_health
                player[3],  # p_damage
                player[4],  # p_armor
                player[5],  # p_speed
                player[6],  # p_break
                player[7],  # p_crit
                player[8],  # p_dodge
                monster[2],  # m_health
                monster[3],  # m_damage
                monster[4],  # m_armor
                monster[5],  # m_tenacity
                monster[6],  # m_speed
                monster[7],  # m_crit
                monster[8],  # m_dodge
                monster[9],  # m_level
                monster[10], # m_currency
                monster[11], # m_modifier
                monster[12]  # m_loot_table_id
            )

            await ctx.send(f"👹 A **{monster[1]}** appeared!")

            asyncio.create_task(self.run_monster_battle(ctx, battle_id))

        except Exception as e:
            return await ctx.send(f"Error: {e}")

async def setup(bot):
    await bot.add_cog(Hunt(bot))
