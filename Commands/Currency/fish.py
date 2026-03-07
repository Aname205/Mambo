import discord
import random
from discord.ext import commands

class Fish(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Initialize a pool
    async def create_pool(self):
        pool = [
            ("Minnow", "🐟", 25, "common", 150, "A tiny fish"),
            ("Minnow", "🐟", 35, "uncommon", 100, "A tiny fish"),
            ("Minnow", "🐟", 40, "rare", 75, "A tiny fish"),
            ("Minnow", "🐟", 50, "epic", 50, "A tiny fish"),
            ("Minnow", "🐟", 60, "legendary", 25, "A tiny fish"),
            ("Bass", "🐠", 80, "common", 125, "A decent catch"),
            ("Bass", "🐠", 90, "uncommon", 90, "A decent catch"),
            ("Bass", "🐠", 100, "rare", 65, "A decent catch"),
            ("Bass", "🐠", 120, "epic", 50, "A decent catch"),
            ("Bass", "🐠", 150, "legendary", 20, "A decent catch"),
            ("Octopus", "🐙", 200, "uncommon", 60, "Squishy"),
            ("Octopus", "🐙", 250, "rare", 45, "Squishy"),
            ("Octopus", "🐙", 350, "epic", 30, "Squishy"),
            ("Octopus", "🐙", 500, "legendary", 15, "Squishy"),
            ("Shark", "🦈", 400, "rare", 35, "Fierce predator"),
            ("Shark", "🦈", 600, "epic", 25, "Fierce predator"),
            ("Shark", "🦈", 900, "legendary", 10, "Fierce predator"),
            ("Kraken", "🦑", 2000, "epic", 25, "Nightmare for those who sails"),
            ("Kraken", "🦑", 4500, "legendary", 5, "Nightmare for those who sails"),
        ]

        for name, emoji, price, tier, fishing_rate, description in pool:
            item_id = await self.bot.db.add_item(name, emoji)
            await self.bot.db.add_fishing_item(item_id, price, tier, fishing_rate, description)

    # Fish
    @commands.command()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def fish(self, ctx):
        pool = await self.bot.db.get_fishing_items()

        if not pool:
            await self.create_pool()
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

    @fish.error
    async def fish_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"Try again in **{error.retry_after:.1f}s**.")

async def setup(bot):
    await bot.add_cog(Fish(bot))
