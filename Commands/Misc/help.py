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
            value="balance, addbalance, subbalance, deposit, withdraw, daily",
            inline=False
        )

        em.add_field(
            name="🎮   **Currency game**",
            value="blackjack, fish, trivia, triviacategories, highlow, rps, lottery, poker, wordle, shop",
            inline=False
        )

        em.add_field(
            name="⚔️   **Battle**",
            value="hunt, duel, monsterinfo",
            inline=False
        )

        em.add_field(
            name="🏪   **Item management**",
            value="iteminfo, buy, sell, inventory, lock, unlock, status",
            inline=False
        )

        em.add_field(
            name="🎉   **Fun**",
            value="waifu",
            inline=False
        )

        await ctx.send(embed=em)

async def setup(bot):
    await bot.add_cog(Help(bot))
