import discord
from discord.ext import commands

class InventoryView(discord.ui.View):
    def __init__(self, ctx, inventory, per_page=8):
        super().__init__(timeout=15)
        self.ctx = ctx
        self.inventory = inventory
        self.per_page = per_page
        self.page = 0
        self.max_pages = (len(self.inventory) - 1) // self.per_page

    # Update embed after hitting a button
    def update_embed(self, ctx):
        em = discord.Embed(
            title=f"{ctx.author.name}'s Inventory",
            color=discord.Color.green()
        )

        start = self.page * self.per_page
        end = start + self.per_page

        for i, (item_id, item_name, item_emoji, item_tier, fishing_price, market_price,
             fishing_description, market_description, is_locked) in enumerate(self.inventory[start:end], start=start+1):

            price = fishing_price if fishing_price is not None else market_price
            description = fishing_description if fishing_description is not None else market_description
            lock_icon = "🔒" if is_locked else ""

            em.add_field(
                name=f"[{i}] {item_tier} {item_name} {item_emoji} {lock_icon}",
                value=f"Price: {price} 🪙 {description}",
                inline=False
            )
        em.set_footer(text=f"Page {self.page+1}/{self.max_pages+1}")
        return em

    # Previous page button
    @discord.ui.button(label="⬅️")
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author:
            await interaction.response.defer()
            return

        if self.page > 0:
            self.page -= 1

        await interaction.response.edit_message(embed=self.update_embed(self.ctx), view=self)

    # Next page button
    @discord.ui.button(label="➡️")
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author:
            await interaction.response.defer()
            return

        if self.page < self.max_pages:
            self.page += 1

        await interaction.response.edit_message(embed=self.update_embed(self.ctx), view=self)

class Inventory(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Show user's inventory
    @commands.command(aliases=["inv","inven"])
    async def inventory(self, ctx):
        inventory = await self.bot.db.get_inventory(ctx.author.id)

        if not inventory:
            em = discord.Embed(
                title=f"{ctx.author.name}'s Inventory",
                description="You don't have any items.",
                color=discord.Color.green()
            )
            return await ctx.send(embed=em)

        view = InventoryView(ctx, inventory)
        await ctx.send(embed=view.update_embed(ctx), view=view)

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
            for id, name, emoji, tier, fishing_price, marker_price, _, _, is_locked in inventory:
                if is_locked:
                    continue  # Skip locked items
                price = fishing_price if fishing_price is not None else marker_price
                if price is None:
                    continue
                amount += price
                item_count += 1

            if item_count == 0:
                return await ctx.send("You don't have any items to sell")

            await self.bot.db.update_wallet(ctx.author.id, amount)
            await self.bot.db.remove_all_from_inventory(ctx.author.id)
            return await ctx.send(f"You sold {item_count} items for {amount} 🪙")

        # Sell by inventory index
        if item_name.isdigit():
            index = int(item_name) - 1

            if index < 0 or index >= len(inventory):
                return await ctx.send("Invalid item index.")

            row = inventory[index]

            item_id, name, emoji, tier, fishing_price, market_price, _, _, is_locked = row
            
            if is_locked:
                return await ctx.send(f"**{tier} {name}** {emoji} is locked and cannot be sold")
            
            price = fishing_price if fishing_price is not None else market_price

            await self.bot.db.update_wallet(ctx.author.id, price)
            await self.bot.db.remove_from_inventory(ctx.author.id, item_id, 1)

            return await ctx.send(f"You sold 1 **{tier} {name}** {emoji} for {price} 🪙" )

        #Selling items by name
        normalized_name = item_name.lower()

        matching_rows = [
            (id, name, emoji, tier, fishing_price, market_price, is_locked)
            for id, name, emoji, tier, fishing_price, market_price, _, _, is_locked in inventory
            if name.lower() == normalized_name
        ]

        if not matching_rows:
            return await ctx.send("You don't have that item in your inventory.")

        # Check if item is locked
        if matching_rows[0][6]:  # is_locked is at index 6
            return await ctx.send(f"**{matching_rows[0][3]} {matching_rows[0][1]}** {matching_rows[0][2]} is locked and cannot be sold. 🔒")

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
        id, name, emoji, tier, fishing_price, market_price, is_locked = matching_rows[0]
        price = fishing_price if fishing_price is not None else market_price

        amount = int(price) * quantity_to_sell

        await self.bot.db.update_wallet(ctx.author.id, amount)
        await self.bot.db.remove_from_inventory(ctx.author.id, id, quantity_to_sell)

        return await ctx.send(f"You sold {quantity_to_sell} **{tier} {name}** {emoji} for {amount}")

    # Lock/Unlock item by index
    @commands.command()
    async def lock(self, ctx, index: int = None):
        if index is None:
            return await ctx.send("Please provide an item index to lock")

        inventory = await self.bot.db.get_inventory(ctx.author.id)

        if not inventory:
            return await ctx.send("You don't have any items")

        index -= 1  # Convert to 0-based index

        if index < 0 or index >= len(inventory):
            return await ctx.send("Invalid item index.")

        row = inventory[index]
        item_id, name, emoji, tier, _, _, _, _, is_locked = row

        if is_locked:
            return await ctx.send(f"**{tier} {name}** {emoji} is already locked")

        await self.bot.db.set_item_lock(item_id, True)
        await ctx.send(f"**{tier} {name}** {emoji} has been locked")

    # Unlock item by index
    @commands.command()
    async def unlock(self, ctx, index: int = None):
        if index is None:
            return await ctx.send("Please provide an item index to unlock")

        inventory = await self.bot.db.get_inventory(ctx.author.id)

        if not inventory:
            return await ctx.send("You don't have any items")

        index -= 1  # Convert to 0-based index

        if index < 0 or index >= len(inventory):
            return await ctx.send("Invalid item index")

        row = inventory[index]
        item_id, name, emoji, tier, _, _, _, _, is_locked = row

        if not is_locked:
            return await ctx.send(f"**{tier} {name}** {emoji} is already unlocked")

        await self.bot.db.set_item_lock(item_id, False)
        await ctx.send(f"**{tier} {name}** {emoji} has been unlocked")

async def setup(bot):
    await bot.add_cog(Inventory(bot))

