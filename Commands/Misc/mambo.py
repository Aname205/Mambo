import discord
from discord.ext import commands

class Mambo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def mambo(self, ctx):
        await ctx.send(f"{ctx.author.mention} Mambo")

async def setup(bot):
    await bot.add_cog(Mambo(bot))
