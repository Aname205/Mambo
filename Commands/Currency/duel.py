import discord
from discord.ext import commands
import asyncio
import random

TURN_DELAY = 1

class Duel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def run_pvp_battle(self, ctx, battle_id):

        battle = await self.bot.db.get_active_pvp_battle(battle_id)

        p1_id = battle[1]
        p2_id = battle[2]

        p1_hp = battle[3]
        p2_hp = battle[4]

        p1_damage = battle[5]
        p2_damage = battle[6]

        p1_armor = battle[7]
        p2_armor = battle[8]

        p1_speed = battle[9]
        p2_speed = battle[10]

        p1_crit = battle[11]
        p2_crit = battle[12]

        p1_dodge = battle[13]
        p2_dodge = battle[14]

        max_gauge = max(p1_speed, p2_speed)

        p1_gauge = 0
        p2_gauge = 0

        battle_log = []

        message = await ctx.send("⚔️ **Battle Started**")

        while p1_hp > 0 and p2_hp > 0:

            if p1_gauge < max_gauge and p2_gauge < max_gauge:
                p1_gauge += p1_speed
                p2_gauge += p2_speed
                continue

            # Decide who acts
            actor = None

            if p1_gauge >= max_gauge and p2_gauge >= max_gauge:
                actor = 1 if p1_gauge >= p2_gauge else 2
            elif p1_gauge >= max_gauge:
                actor = 1
            elif p2_gauge >= max_gauge:
                actor = 2

            # PLAYER 1 TURN
            if actor == 1:

                p1_gauge -= max_gauge

                if random.random() < p2_dodge:
                    battle_log.append(f"<@{p1_id}> attacked but <@{p2_id}> **dodged** 👟")
                else:

                    base_damage = p1_damage - p2_armor
                    if base_damage < 0:
                        base_damage = 0
                    damage = int(base_damage * random.uniform(0.8, 1.2))

                    if random.random() < p1_crit:
                        damage *= 2
                        crit = "💥 **CRIT**"
                    else:
                        crit = ""

                    p2_hp -= damage

                    battle_log.append(
                        f"<@{p1_id}> hits <@{p2_id}> for **{damage}** damage {crit}"
                    )

                await asyncio.sleep(TURN_DELAY)

            # PLAYER 2 TURN
            if actor == 2:

                p2_gauge -= max_gauge

                if random.random() < p1_dodge:
                    battle_log.append(f"<@{p2_id}> attacked but <@{p1_id}> **dodged** 👟")
                else:

                    base_damage = p2_damage - p1_armor
                    if base_damage < 0:
                        base_damage = 0
                    damage = int(base_damage * random.uniform(0.8, 1.2))

                    if random.random() < p2_crit:
                        damage *= 2
                        crit = "💥 **CRIT**"
                    else:
                        crit = ""

                    p1_hp -= damage

                    battle_log.append(
                        f"<@{p2_id}> hits <@{p1_id}> for **{damage}** damage {crit}"
                    )

                await asyncio.sleep(TURN_DELAY)

            # Update battle embed
            embed = discord.Embed(
                title="⚔️ PvP Battle",
                description="\n".join(battle_log[-6:]),
                color=discord.Color.red()
            )

            embed.add_field(name="Player 1 HP", value=f"<@{p1_id}> ❤️ {p1_hp}")
            embed.add_field(name="Player 2 HP", value=f"<@{p2_id}> ❤️ {p2_hp}")

            await message.edit(embed=embed)

            if p1_hp <= 0 or p2_hp <= 0:
                break

        # Winner
        if p1_hp <= 0:
            winner_text = f"🏆 <@{p2_id}> wins the duel"
            await self.bot.db.end_pvp_battle(battle_id, "player_2_won")
        else:
            winner_text = f"🏆 <@{p1_id}> wins the duel"
            await self.bot.db.end_pvp_battle(battle_id, "player_1_won")

        battle_log.append("")
        battle_log.append(winner_text)

        embed = discord.Embed(
            title="⚔️ PvP Battle Finished",
            description="\n".join(battle_log[-10:]),
            color=discord.Color.gold()
        )

        embed.add_field(name="Player 1 HP", value=f"<@{p1_id}> ❤️ {max(0, p1_hp)}")
        embed.add_field(name="Player 2 HP", value=f"<@{p2_id}> ❤️ {max(0, p2_hp)}")

        await message.edit(embed=embed)


    @commands.command()
    async def duel(self,ctx, opponent: discord.Member):
        try:
            if opponent.bot:
                await ctx.send("You can't duel a bot")
                return

            if opponent.id == ctx.author.id:
                await ctx.send("You can't duel yourself")
                return

            p1 = await self.bot.db.get_player(ctx.author.id)
            p2 = await self.bot.db.get_player(opponent.id)

            battle_id = await self.bot.db.start_pvp_battle(
                ctx.author.id,
                opponent.id,
                p1[2],
                p2[2],
                p1[3],
                p2[3],
                p1[4],
                p2[4],
                p1[5],
                p2[5],
                p1[7],
                p2[7],
                p1[8],
                p2[8]
            )

            await ctx.send(
                f"⚔️ {ctx.author.mention} challenged {opponent.mention}"
            )

            asyncio.create_task(self.run_pvp_battle(ctx, battle_id))

        except Exception as e:
            return await ctx.send(f"Error: {e}")

async def setup(bot):
    await bot.add_cog(Duel(bot))