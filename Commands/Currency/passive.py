import discord
from discord.ext import commands

from Database.data.passive_data import weapon_passives


class TestPassive(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="testpassive", aliases=["tp"])
    async def testpassive(self, ctx, *effects: str):
        """List available passives. Usage: mtestpassive list"""
        lines = [f"`{e[0]}` — {e[2]} ({e[1]})" for e in weapon_passives]
        embed = discord.Embed(
            title="🧪 Available Passives",
            description="\n".join(lines),
            color=discord.Color.blurple()
        )
        return await ctx.send(embed=embed)

        # ── Disabled: give Wooden Sword with passives ──────────────────────────
        # effect_names = [e.lower() for e in effects]
        #
        # passive_rows = []
        # not_found = []
        # for effect in effect_names:
        #     async with self.bot.db.db.cursor() as cursor:
        #         await cursor.execute(
        #             "SELECT id, effect, emoji, affix_suffix FROM passives WHERE effect = ?",
        #             (effect,)
        #         )
        #         row = await cursor.fetchone()
        #     if row:
        #         passive_rows.append(row)
        #     else:
        #         not_found.append(effect)
        #
        # if not_found:
        #     return await ctx.send(
        #         f"❌ Effect(s) not found: {', '.join(f'`{e}`' for e in not_found)}\n"
        #         f"Use `mtestpassive list` to see all. Tip: run `mensurepassives` first."
        #     )
        #
        # async with self.bot.db.db.cursor() as cursor:
        #     await cursor.execute(
        #         "SELECT id FROM items WHERE name = 'Wooden Sword' AND item_type = 'equipment'",
        #     )
        #     item_row = await cursor.fetchone()
        #
        # if not item_row:
        #     return await ctx.send("❌ Wooden Sword not found in items table.")
        #
        # item_id = item_row[0]
        #
        # async with self.bot.db.db.cursor() as cursor:
        #     await cursor.execute(
        #         "INSERT INTO inventories(user_id, item_id, item_tier, amount) VALUES (?, ?, 'common', 1)",
        #         (ctx.author.id, item_id)
        #     )
        #     await self.bot.db.db.commit()
        #     inventory_id = cursor.lastrowid
        #
        # for row in passive_rows:
        #     await self.bot.db.add_item_passive(inventory_id, row[0])
        #
        # affix_names = " ".join(r[3] for r in passive_rows)
        # passive_list = "\n".join(f"{r[2]} **{r[1]}**" for r in passive_rows)
        #
        # embed = discord.Embed(title="🧪 Test Weapon Given", color=discord.Color.green())
        # embed.add_field(
        #     name="Weapon",
        #     value=f"🗡️ **common {affix_names} Wooden Sword**\n`inventory_id: {inventory_id}`",
        #     inline=False
        # )
        # embed.add_field(name="Passive(s)", value=passive_list, inline=False)
        # embed.set_footer(text="Equip manually to test in battle.")
        # await ctx.send(embed=embed)
        # ── End disabled ───────────────────────────────────────────────────────

async def setup(bot):
    await bot.add_cog(TestPassive(bot))
