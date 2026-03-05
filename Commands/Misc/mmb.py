import discord
from discord.ext import commands

class Mmb(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def mb(self, ctx):
        await ctx.send(f"{ctx.author.mention} Me may beo")

async def setup(bot):
    await bot.add_cog(Mmb(bot))
