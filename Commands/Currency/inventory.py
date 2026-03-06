import discord
from discord.ext import commands

class Inventory(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Show user's inventory
    @commands.command(aliases=["inv","inven"])
    async def inventory(self, ctx):
        inventory = await self.bot.db.get_inventory(ctx.author.id)

        em = discord.Embed(
            title=f"{ctx.author.name}'s Inventory",
            color=discord.Color.green()
        )

        if not inventory:
            em.description="You don't have any items."

        for item_id, item_name, item_emoji, fishing_price, market_price in inventory:

            if fishing_price is not None:
                price = fishing_price
            elif market_price is not None:
                price = market_price

            em.add_field(
                name=f"{item_name} {item_emoji}",
                value=f"Price: {price} 🪙, ID: {item_id}",
                inline=False
            )
        await ctx.send(embed=em)


    # Selling items
    @commands.command()
    async def sell(self, ctx, item_name: str = None, item_amount: int = None):
        inventory = await self.bot.db.get_inventory(ctx.author.id)

        if not inventory:
            return await ctx.send("You don't have any items")

        if item_name is None:
            return await ctx.send(f"Please name an item to sell")

        # Sell all items
        if str(item_name).lower() == 'all' and item_amount is None:
            amount = 0
            item_count = 0
            for id, name, emoji, fishing_price, marker_price in inventory:
                price = fishing_price if fishing_price is not None else marker_price
                if price is None:
                    continue
                amount += price
                item_count += 1

            await self.bot.db.update_wallet(ctx.author.id, amount)
            await self.bot.db.remove_all_from_inventory(ctx.author.id)
            return await ctx.send(f"You sold {item_count} items for {amount} 🪙")

        #Selling items by name
        normalized_name = item_name.lower()

        matching_rows = [
            (id, name, emoji, fishing_price, market_price)
            for id, name, emoji, fishing_price, market_price in inventory
            if name.lower() == normalized_name
        ]

        if not matching_rows:
            return await ctx.send("You don't have that item in your inventory.")

        # Determine how many to sell
        if item_amount is None:
            quantity_to_sell = 1
        else:
            if item_amount <= 0:
                return await ctx.send("Amount to sell must be greater than 0.")
            quantity_to_sell = item_amount

        available_count = len(matching_rows)
        if quantity_to_sell > available_count:
            return await ctx.send(f"You don't have enough {item_name}.")

        # All copies share the same price, get it from the first row
        id, name, emoji, fishing_price, market_price = matching_rows[0]
        price = fishing_price if fishing_price is not None else market_price

        amount = int(price) * quantity_to_sell

        await self.bot.db.update_wallet(ctx.author.id, amount)
        await self.bot.db.remove_from_inventory(ctx.author.id, id, quantity_to_sell)

        return await ctx.send(f"You sold {quantity_to_sell} **{name}** {emoji} for {amount}")

async def setup(bot):
    await bot.add_cog(Inventory(bot))

