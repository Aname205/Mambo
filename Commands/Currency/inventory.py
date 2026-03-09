import discord
from discord.ext import commands
class InventorySelect(discord.ui.Select):
    def __init__(self, view):
        self.parent_view = view

        start = view.page * view.per_page
        end = start + view.per_page

        options = []

        for i, row in enumerate(view.inventory[start:end], start=start):
            inv_id, item_id, name, emoji, tier, *_ , is_locked = row

            lock = "🔒 " if is_locked else ""

            options.append(
                discord.SelectOption(
                    label=f"[{i+1}] {tier} {name} {lock}",
                    description="",
                    emoji=emoji,
                    value=str(i)
                )
            )

        super().__init__(
            placeholder="Select an item...",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):

        if interaction.user != self.parent_view.ctx.author:
            await interaction.response.defer()
            return

        self.parent_view.selected = int(self.values[0])

        await interaction.response.edit_message(
            embed=self.parent_view.update_embed(self.parent_view.ctx),
            view=self.parent_view
        )

class InventoryView(discord.ui.View):
    def __init__(self, ctx, inventory, per_page=8):
        super().__init__(timeout=15)
        self.ctx = ctx
        self.inventory = inventory
        self.per_page = per_page
        self.page = 0
        self.selected = 0
        self.add_item(InventorySelect(self))
        self.max_pages = max(0, (len(self.inventory) - 1) // self.per_page)

    # Update embed after hitting a button
    def update_embed(self, ctx, message=None):
        em = discord.Embed(
            color=discord.Color.green()
        )
        em.set_author(name=f"{ctx.author.name}'s Inventory", icon_url=ctx.author.display_avatar.url)

        start = self.page * self.per_page
        end = start + self.per_page

        for i, (inv_id, item_id, item_name, item_emoji, item_tier, fishing_price, market_price,
             fishing_description, market_description, is_locked) in enumerate(self.inventory[start:end], start=start):

            left_pointer = "⭐ " if i == self.selected else ""
            right_pointer = " ⭐" if i == self.selected else ""

            price = fishing_price if fishing_price is not None else market_price
            description = fishing_description if fishing_description is not None else market_description
            lock_icon = "🔒" if is_locked else ""

            em.add_field(
                name=f"{left_pointer} [{i+1}] {item_tier} {item_name} {item_emoji} {lock_icon} {right_pointer}",
                value=f"Price: {price} 🪙 {description}",
                inline=False
            )
        em.set_footer(text=f"Page {self.page+1}/{self.max_pages+1}")

        if message:
            em.add_field(
                name = "",
                value = message,
                inline = False
            )

        return em

    #Refresh select menu when page change
    def refresh_select(self):
        for item in self.children:
            if isinstance(item, InventorySelect):
                self.remove_item(item)

        self.add_item(InventorySelect(self))

    # Previous page button
    @discord.ui.button(label="⬅️")

    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author:
            await interaction.response.defer()
            return

        if self.page > 0:
            self.page -= 1
            self.selected = self.per_page * self.page
            self.refresh_select()

        await interaction.response.edit_message(embed=self.update_embed(self.ctx), view=self)

    # Next page button
    @discord.ui.button(label="➡️")
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author:
            await interaction.response.defer()
            return

        if self.page < self.max_pages:
            self.page += 1
            self.selected = self.per_page * self.page
            self.refresh_select()

        await interaction.response.edit_message(embed=self.update_embed(self.ctx), view=self)

    @discord.ui.button(label="💰", style=discord.ButtonStyle.blurple)
    async def sell_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author:
            await interaction.response.defer()
            return

        row = self.inventory[self.selected]

        inv_id, item_id, name, emoji, tier, fishing_price, market_price, _, _, is_locked = row

        if is_locked:
            message = f"**This item is locked and cannot be sold**"
            await interaction.response.edit_message(embed=self.update_embed(self.ctx, message), view=self)
            return

        price = fishing_price if fishing_price is not None else market_price

        await self.ctx.bot.db.update_wallet(self.ctx.author.id, price)
        await self.ctx.bot.db.remove_from_inventory(self.ctx.author.id, item_id, 1)

        self.inventory.pop(self.selected)

        if not self.inventory:
            em = discord.Embed(
                description=f"**You sold 1 {tier} {name} {emoji} for {price} 🪙**\n\nYour inventory is empty",
                color=discord.Color.green()
            )
            em.set_author(name=f"{self.ctx.author.name}'s Inventory",icon_url=self.ctx.author.display_avatar.url)

            await interaction.response.edit_message(embed=em,view=None)
            self.stop()
            return

        self.max_pages = max(0, (len(self.inventory) - 1) // self.per_page)

        if self.selected >= len(self.inventory):
            self.selected = max(0, len(self.inventory) - 1)

        self.refresh_select()

        message = f"**You sold 1 {tier} {name} {emoji} for {price} 🪙**"

        await interaction.response.edit_message(embed=self.update_embed(self.ctx, message), view=self)

    @discord.ui.button(label="🔒", style=discord.ButtonStyle.green)
    async def lock_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author:
            await interaction.response.defer()
            return

        row = self.inventory[self.selected]
        inv_id, item_id, name, emoji, tier, _, _, _, _, is_locked = row

        if is_locked:
            message = "**This item is already locked**"
            await interaction.response.edit_message(embed=self.update_embed(self.ctx, message), view=self)
            return

        await self.ctx.bot.db.set_item_lock(inv_id, True)

        row = list(self.inventory[self.selected])
        row[9] = True
        self.inventory[self.selected] = tuple(row)
        self.refresh_select()

        message = f"**You have locked {tier} {name} {emoji}**"

        await interaction.response.edit_message(embed=self.update_embed(self.ctx, message), view=self)

    @discord.ui.button(label="🔓", style=discord.ButtonStyle.red)
    async def unlock_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author:
            await interaction.response.defer()
            return

        row = self.inventory[self.selected]
        inv_id, item_id, name, emoji, tier, _, _, _, _, is_locked = row

        if not is_locked:
            message = "**This item is already unlocked**"
            await interaction.response.edit_message(embed=self.update_embed(self.ctx, message), view=self)
            return

        await self.ctx.bot.db.set_item_lock(inv_id, False)

        row = list(self.inventory[self.selected])
        row[9] = False
        self.inventory[self.selected] = tuple(row)
        self.refresh_select()

        message = f"**You have unlocked {tier} {name} {emoji}**"

        await interaction.response.edit_message(embed=self.update_embed(self.ctx, message), view=self)

class Inventory(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Show user's inventory
    @commands.command(aliases=["inv","inven"])
    async def inventory(self, ctx):
        inventory = await self.bot.db.get_inventory(ctx.author.id)

        if not inventory:
            em = discord.Embed(
                description="You don't have any items.",
                color=discord.Color.green()
            )
            em.set_author(name=f"{ctx.author.name}'s Inventory", icon_url=ctx.author.display_avatar.url)
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
            for inv_id, item_id, name, emoji, tier, fishing_price, marker_price, _, _, is_locked in inventory:
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

            inv_id, item_id, name, emoji, tier, fishing_price, market_price, _, _, is_locked = row
            
            if is_locked:
                return await ctx.send(f"**{tier} {name}** {emoji} is locked and cannot be sold")
            
            price = fishing_price if fishing_price is not None else market_price

            await self.bot.db.update_wallet(ctx.author.id, price)
            await self.bot.db.remove_from_inventory(ctx.author.id, item_id, 1)

            return await ctx.send(f"You sold 1 **{tier} {name}** {emoji} for {price} 🪙" )

        #Selling items by name
        normalized_name = item_name.lower()

        matching_rows = [
            (inv_id, item_id, name, emoji, tier, fishing_price, market_price, is_locked)
            for inv_id, item_id, name, emoji, tier, fishing_price, market_price, _, _, is_locked in inventory
            if name.lower() == normalized_name
        ]

        if not matching_rows:
            return await ctx.send("You don't have that item in your inventory.")

        # Check if item is locked
        if matching_rows[0][7]:  # is_locked is at index 7
            return await ctx.send(f"**{matching_rows[0][4]} {matching_rows[0][2]}** {matching_rows[0][3]} is locked and cannot be sold. 🔒")

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
        inv_id, item_id, name, emoji, tier, fishing_price, market_price, is_locked = matching_rows[0]
        price = fishing_price if fishing_price is not None else market_price

        amount = int(price) * quantity_to_sell

        await self.bot.db.update_wallet(ctx.author.id, amount)
        await self.bot.db.remove_from_inventory(ctx.author.id, item_id, quantity_to_sell)

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
        inv_id, item_id, name, emoji, tier, _, _, _, _, is_locked = row

        if is_locked:
            return await ctx.send(f"**{tier} {name}** {emoji} is already locked")

        await self.bot.db.set_item_lock(inv_id, True)
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
        inv_id, item_id, name, emoji, tier, _, _, _, _, is_locked = row

        if not is_locked:
            return await ctx.send(f"**{tier} {name}** {emoji} is already unlocked")

        await self.bot.db.set_item_lock(inv_id, False)
        await ctx.send(f"**{tier} {name}** {emoji} has been unlocked")

async def setup(bot):
    await bot.add_cog(Inventory(bot))

