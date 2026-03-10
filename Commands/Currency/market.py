import discord
from discord.ext import commands
from flask import ctx


class MarketSelect(discord.ui.Select):
    def __init__(self, view):
        self.parent_view = view

        start = view.page * view.per_page
        end = start + view.per_page

        options = []

        for i ,row in enumerate(view.market[start:end], start=start):
            eq_id, name, emoji, eq_type, dmg, armor, speed, break_force, _, price, crit, dodge = row

            options.append(
                discord.SelectOption(
                    label=f"[{i+1}] {name}",
                    description="",
                    emoji=emoji,
                    value=str(i),
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

class MarketView(discord.ui.View):
    def __init__(self, ctx, market, inventory, per_page=6):
        super().__init__(timeout=15)

        self.ctx = ctx
        self.market = market
        self.inventory = inventory
        self.per_page = per_page
        self.page = 0
        self.selected = 0
        self.add_item(MarketSelect(self))
        self.max_pages = max(0,(len(self.market) - 1) // self.per_page)

    def update_embed(self, ctx, message=None):
        try:
            em = discord.Embed(
                color=discord.Color.green()
            )
            em.set_author(name=f"{ctx.author.name} is in the market", icon_url=ctx.author.display_avatar.url)

            start = self.page * self.per_page
            end = start + self.per_page

            for i, (eq_id, name, emoji, eq_type, dmg, armor, speed, break_force, _, price, crit, dodge) \
                in (enumerate(self.market[start:end], start=start)):

                pointer = "⭐ " if i == self.selected else ""

                stats = []

                if dmg:
                    stats.append(f"🗡️ **{dmg}**")
                if armor:
                    stats.append(f"🛡 **{armor}**")
                if speed:
                    stats.append(f"💨 **{speed}**")
                if break_force:
                    stats.append(f"⚡ **{break_force}**")
                if crit:
                    stats.append(f"🎯 **{crit * 100:.0f}%**")
                if dodge:
                    stats.append(f"👟 **{dodge * 100:.0f}%**")

                stat_text = " ".join(stats)

                em.add_field(
                    name=f"{pointer} [{i+1}] {name} {emoji}",
                    value=f"{stat_text}\n💰 Price: {price} 🪙",
                    inline=True
                )

            em.set_footer(text=f"Page {self.page + 1}/{self.max_pages+1}")

            if message:
                em.add_field(
                    name = "",
                    value = message,
                    inline = False
                )

            return em

        except Exception as e:
            self.ctx.send(f"Error: {e}")

    # Refresh select menu when page change
    def refresh_select(self):
        for item in self.children:
            if isinstance(item, MarketSelect):
                self.remove_item(item)

                self.add_item(MarketSelect(self))

    @discord.ui.button(label="➡️")
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author:
            await interaction.response.defer()
            return

        if self.page < self.max_pages:
            self.page += 1
            self.selected = self.per_page * self.page
            self.refresh_select()

        else:
            self.page = 0
            self.selected = self.per_page * self.page
            self.refresh_select()

        await interaction.response.edit_message(embed=self.update_embed(self.ctx), view=self)

    @discord.ui.button(label="⬅️")
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author:
            await interaction.response.defer()
            return

        if self.page > 0:
            self.page -= 1
            self.selected = self.per_page * self.page
            self.refresh_select()

        else:
            self.page += self.max_pages
            self.selected = self.per_page * self.page
            self.refresh_select()

        await interaction.response.edit_message(embed=self.update_embed(self.ctx), view=self)

    @discord.ui.button(label="💰", style=discord.ButtonStyle.green)
    async def buy(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            if interaction.user != self.ctx.author:
                await interaction.response.defer()
                return

            row = self.market[self.selected]
            balance = await self.ctx.bot.db.get_balance(self.ctx.author.id)

            wallet = balance[0]

            item_id, name, emoji, eq_type, dmg, armor, speed, break_force, tier, price, crit, dodge = row

            if wallet < price:
                message = "**You don't have enough money**"
                await interaction.response.edit_message(embed=self.update_embed(self.ctx, message), view=self)
                return

            await self.ctx.bot.db.update_wallet(self.ctx.author.id, -price)
            await self.ctx.bot.db.add_to_inventory(self.ctx.author.id, item_id, tier)

            self.inventory = await self.ctx.bot.db.get_inventory(self.ctx.author.id)

            message = f"**You bought {name} {emoji} for {price} 🪙**"
            await interaction.response.edit_message(embed=self.update_embed(self.ctx, message), view=self)

        except Exception as e:
            await interaction.response.edit_message(embed=self.update_embed(self.ctx, e), view=self)

class Market(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def market(self, ctx):

        try:
            market = await self.bot.db.get_market_equipments()
            inventory = await self.bot.db.get_inventory(ctx.author.id)

            view = MarketView(ctx, market, inventory)
            await ctx.send(embed=view.update_embed(ctx), view=view)

        except Exception as e:
            await ctx.send(f"Error: {e}")

async def setup(bot):
    await bot.add_cog(Market(bot))