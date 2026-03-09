import discord
from discord.ext import commands

class Daily(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.cooldown(1, 82800, commands.BucketType.user)
    async def daily(self, ctx):
        await self.bot.db.update_wallet(ctx.author.id, 1000)
        await ctx.send("You've received your daily 1000 🪙")

    @daily.error
    async def daily_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            seconds = int(error.retry_after)
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            secs = seconds % 60
            await ctx.send(f"You can receive your daily again after **{hours}h {minutes}m {secs}s**.")

async def setup(bot):
    await bot.add_cog(Daily(bot))