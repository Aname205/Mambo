import discord
from discord.ext import commands

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def help(self, ctx):
        em = discord.Embed(title="**Command List**", color=discord.Color.blue())

        em.add_field(
            name="💰   **Currency**",
            value="balance, addbalance, subbalance, deposit, withdraw",
            inline=False
        )

        em.add_field(
            name="🎮   **Currency game**",
            value="blackjack, fish, trivia, triviacategories",
            inline=False
        )

        em.add_field(
            name="🏪   **Item management**",
            value="items, iteminfo, clearitem, sell",
            inline=False
        )

        await ctx.send(embed=em)

async def setup(bot):
    await bot.add_cog(Help(bot))
