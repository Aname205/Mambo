import discord
import random
from discord.ext import commands

class Fish(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Fish
    @commands.command()
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def fish(self, ctx):
        try:
            pool = await self.bot.db.get_fishing_items()

            ids = [row[0] for row in pool]
            names = [row[1] for row in pool]
            emojis = [row[2] for row in pool]
            tier = [row[3] for row in pool]
            weights = [float(row[4]) for row in pool]
            chosen = random.choices(range(len(pool)), weights=weights, k=1)[0]
            item_id, item_name, item_emoji, item_tier = ids[chosen], names[chosen], emojis[chosen], tier[chosen]
            await self.bot.db.add_to_inventory(ctx.author.id, item_id)

            await ctx.send(f"You reeled in **{item_tier} {item_name}** {item_emoji}")
        except Exception as e:
            await ctx.send(f"Error: {e}")

    @fish.error
    async def fish_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"Try again in **{error.retry_after:.1f}s**.")

async def setup(bot):
    await bot.add_cog(Fish(bot))
