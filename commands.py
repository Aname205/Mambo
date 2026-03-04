import discord
from discord.ext import commands

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def balance(self, ctx):
        wallet, bank = await self.bot.db.get_balance(ctx.author.id)

        em = discord.Embed(
            title=f"{ctx.author.name}'s Balance",
            color=discord.Color.blue()
        )
        em.add_field(name="Wallet", value=wallet)
        em.add_field(name="Bank", value=bank)

        await ctx.send(embed=em)

    @commands.command()
    async def mambo(self, ctx):
        await ctx.send(f"{ctx.author.mention} Mambo")

async def setup(bot):
    await bot.add_cog(Economy(bot))