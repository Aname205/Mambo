import discord
from discord.ext import commands

class Items(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Show the list of items
    @commands.command()
    async def items(self, ctx):
        items = await self.bot.db.get_all_items()

        em = discord.Embed(title="Items", color=discord.Color.green())

        for item_id, item_name, item_emoji in items:
            em.add_field(
                name=f"{item_name} {item_emoji}",
                value=f"ID: {item_id}",
                inline=False
            )

        await ctx.send(embed=em)

    # Show info of one item by name
    @commands.command(aliases=["if"])
    async def iteminfo(self, ctx, item_name: str = None):
        if item_name is None:
            return await ctx.send("Please name the item you are looking for")

        item = await self.bot.db.get_item_by_name(item_name)

        if not item:
            return await ctx.send("Item not found")

        for id, name, emoji, fishing_price, fishing_description, market_price, market_description in item:
            em = discord.Embed(title=f"**{item_name}** {emoji}", color=discord.Color.yellow())

            if fishing_price is not None:
                em.add_field(name="Price:", value=f"{fishing_price} 🪙", inline=False)
                em.add_field(name="Description:", value=fishing_description, inline=False)
            else:
                em.add_field(name="Price:", value=f"{market_price} 🪙", inline=False)
                em.add_field(name="Description:", value=market_description, inline=False)

        return await ctx.send(embed=em)

    # Clear all items in the database
    @commands.command()
    async def clearitem(self, ctx):
        await self.bot.db.clear_all_items()
        return await ctx.send("Cleared all items")

async def setup(bot):
    await bot.add_cog(Items(bot))