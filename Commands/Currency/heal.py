import discord
from discord.ext import commands
import asyncio

class HealConfirmView(discord.ui.View):
    def __init__(self, ctx, heal_cost):
        super().__init__(timeout=30)
        self.ctx = ctx
        self.heal_cost = heal_cost
        self.confirmed = False

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message("This is not your confirmation prompt.", ephemeral=True)

        self.confirmed = True
        self.stop()
        await interaction.response.defer()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message("This is not your confirmation prompt.", ephemeral=True)

        self.confirmed = False
        self.stop()
        await interaction.response.defer()

class Heal(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def heal(self, ctx):
        player = await self.bot.db.players.get_player(ctx.author.id)
        max_health = player[2]
        current_health = player[24] if player[24] is not None else max_health

        if current_health >= max_health:
            return await ctx.send("You are already at full health!")

        missing_health = max_health - current_health
        
        if max_health < 1000:
            heal_cost = missing_health
        else:
            base_cost = 1.0  # Use float for calculation
            missing_ratio = missing_health / max_health
            # The cost should be per point of health, not multiplied by it
            heal_cost = int(base_cost * (1 + (missing_ratio * 5) ** 2) * missing_health)


        wallet, _ = await self.bot.db.get_balance(ctx.author.id)

        if wallet < heal_cost:
            return await ctx.send(f"You need {heal_cost} coins to heal, but you only have {wallet} coins.")

        view = HealConfirmView(ctx, heal_cost)
        message = await ctx.send(f"Are you sure you want to heal {missing_health} HP for {heal_cost} coins?", view=view)

        await view.wait()

        if view.confirmed:
            await self.bot.db.update_wallet(ctx.author.id, -heal_cost)
            await self.bot.db.players.update_current_health(ctx.author.id, max_health)
            await message.edit(content=f"You have been healed to full health for {heal_cost} coins.", view=None)
        else:
            await message.edit(content="Healing cancelled.", view=None)

async def setup(bot):
    await bot.add_cog(Heal(bot))
