import discord
import random
from discord.ext import commands

class Fish(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Initialize a pool
    async def create_pool(self):
        pool = [
            ("Minnow", "🐟", 50, "common", 0.40, "A tiny fish"),
            ("Bass", "🐠", 120, "common", 0.35, "A decent catch"),
            ("Octopus", "🐙", 250, "uncommon", 0.15, "Squishy"),
            ("Shark", "🦈", 500, "rare", 0.07, "Fierce predator"),
            ("Kraken", "🦑", 2000, "legendary", 0.03, "Nightmare for those who sails"),
        ]

        for name, emoji, price, tier, fishing_rate, description in pool:
            item_id = await self.bot.db.add_item(name, emoji)
            await self.bot.db.add_fishing_item(item_id, price, tier, fishing_rate, description)

    # Fish
    @commands.command()
    async def fish(self, ctx):
        pool = await self.bot.db.get_fishing_items()

        if not pool:
            await self.create_pool()
            pool = await self.bot.db.get_fishing_items()

        ids = [row[0] for row in pool]
        names = [row[1] for row in pool]
        emojis = [row[2] for row in pool]
        weights = [float(row[3]) for row in pool]
        chosen = random.choices(range(len(pool)), weights=weights, k=1)[0]
        item_id, item_name, item_emoji = ids[chosen], names[chosen], emojis[chosen]
        await self.bot.db.add_to_inventory(ctx.author.id, item_id)

        await ctx.send(f"You reeled in **{item_name}** {item_emoji}")

async def setup(bot):
    await bot.add_cog(Fish(bot))
