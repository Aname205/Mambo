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

        for item_id, item_name, item_emoji, item_type in items:
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

        try:
            items = await self.bot.db.get_item_by_name(item_name)

            if not items:
                return await ctx.send("Item not found")

            first_item = items[0]
            _, name, emoji, _, fishing_description, _, market_description, _ = first_item
            description = fishing_description if fishing_description is not None else market_description

            em = discord.Embed(
                title=f"{name} {emoji}",
                color=discord.Color.yellow()
            )

            em.set_footer(text=description)

            # Collect all tiers and prices
            tiers_list = []
            prices_list = []
            
            for item_data in items:
                id, name, emoji, fishing_price, _, market_price, _, tier = item_data
                
                if tier:
                    price = fishing_price if fishing_price is not None else market_price
                    
                    tiers_list.append(tier)
                    prices_list.append(f"{price} 🪙")

            if tiers_list:
                em.add_field(name="Tiers", value="\n".join(tiers_list), inline=True)
                em.add_field(name="Prices", value="\n".join(prices_list), inline=True)

            return await ctx.send(embed=em)
        except Exception as e:
            return await ctx.send(f"Error: {e}")

    # Clear all items in the database
    @commands.command()
    async def clearitem(self, ctx):
        await self.bot.db.clear_all_items()
        return await ctx.send("Cleared all items")

async def setup(bot):
    await bot.add_cog(Items(bot))