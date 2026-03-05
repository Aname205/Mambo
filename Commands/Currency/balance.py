import discord
from discord.ext import commands

class Balance(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def balance(self, ctx):
        in_hand, in_bank = await self.bot.db.get_balance(ctx.author.id)

        em = discord.Embed(
            title=f"{ctx.author.name}'s Balance",
            color=discord.Color.blue()
        )
        em.add_field(name="💰 In Hand", value=f"{in_hand:,}")
        em.add_field(name="🏦 In Bank", value=f"{in_bank:,}")

        await ctx.send(embed=em)

async def setup(bot):
    await bot.add_cog(Balance(bot))