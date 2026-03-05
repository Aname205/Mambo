import discord
from discord.ext import commands

class Balance(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def _get_author_avatar_url(self, ctx):
        return ctx.author.display_avatar.url

    @commands.command(aliases=["bal"])
    async def balance(self, ctx):
        in_hand, in_bank = await self.bot.db.get_balance(ctx.author.id)

        em = discord.Embed(color=discord.Color.blue())
        em.set_author(name=f"{ctx.author.name}'s Balance", icon_url=self._get_author_avatar_url(ctx))
        em.add_field(name="💰 In Hand", value=f":coin: {in_hand:,} ", inline=False)
        em.add_field(name="🏦 In Bank", value=f":coin: {in_bank:,} ", inline=False)

        await ctx.send(embed=em)

    @commands.command(name="addbalance", aliases=["ab"])
    async def add_money(self, ctx, amount: int = None):
        if amount is None:
            return await ctx.send("Please enter an amount to add.")
        if amount <= 0:
            return await ctx.send("Amount must be greater than 0.")

        await self.bot.db.update_wallet(ctx.author.id, amount)
        in_hand, _ = await self.bot.db.get_balance(ctx.author.id)

        em = discord.Embed(title="Money Added", color=discord.Color.green())
        em.description = f"Added **{amount:,} :coin:** to your wallet.\nCurrent wallet: **{in_hand:,} :coin:**"
        await ctx.send(embed=em)

    @commands.command(name="subbalance", aliases=["sb"])
    async def sub_money(self, ctx, amount: int = None):
        if amount is None:
            return await ctx.send("Please enter an amount to subtract.")
        if amount <= 0:
            return await ctx.send("Amount must be greater than 0.")

        in_hand, _ = await self.bot.db.get_balance(ctx.author.id)
        if in_hand < amount:
            return await ctx.send("You do not have enough money in your wallet.")

        await self.bot.db.update_wallet(ctx.author.id, -amount)
        updated_in_hand, _ = await self.bot.db.get_balance(ctx.author.id)

        em = discord.Embed(title="Money Subtracted", color=discord.Color.red())
        em.description = f"Subtracted **{amount:,} :coin:** from your wallet.\nCurrent wallet: **{updated_in_hand:,} :coin:**"
        await ctx.send(embed=em)

    @commands.command(name="deposit", aliases=["dep"])
    async def deposit(self, ctx, amount: int = None):
        if amount is None:
            return await ctx.send("Please enter an amount to deposit.")
        if amount <= 0:
            return await ctx.send("Amount must be greater than 0.")

        in_hand, _ = await self.bot.db.get_balance(ctx.author.id)
        if in_hand < amount:
            return await ctx.send("You do not have enough money in hand.")

        await self.bot.db.update_wallet(ctx.author.id, -amount)
        await self.bot.db.update_bank(ctx.author.id, amount)
        updated_hand, updated_bank = await self.bot.db.get_balance(ctx.author.id)

        em = discord.Embed(title="Deposit Successful", color=discord.Color.gold())
        em.description = (
            f"Deposited **{amount:,} :coin:** to your bank.\n"
            f"In Hand: **{updated_hand:,} :coin:**\n"
            f"In Bank: **{updated_bank:,} :coin:**"
        )
        await ctx.send(embed=em)

    @commands.command(name="withdraw", aliases=["wd"])
    async def withdraw(self, ctx, amount: int = None):
        if amount is None:
            return await ctx.send("Please enter an amount to withdraw.")
        if amount <= 0:
            return await ctx.send("Amount must be greater than 0.")

        _, in_bank = await self.bot.db.get_balance(ctx.author.id)
        if in_bank < amount:
            return await ctx.send("You do not have enough money in bank.")

        await self.bot.db.update_bank(ctx.author.id, -amount)
        await self.bot.db.update_wallet(ctx.author.id, amount)
        updated_hand, updated_bank = await self.bot.db.get_balance(ctx.author.id)

        em = discord.Embed(title="Withdrawal Successful", color=discord.Color.purple())
        em.description = (
            f"Withdrew **{amount:,} :coin:** to your hand.\n"
            f"In Hand: **{updated_hand:,} :coin:**\n"
            f"In Bank: **{updated_bank:,} :coin:**"
        )
        await ctx.send(embed=em)

async def setup(bot):
    await bot.add_cog(Balance(bot))