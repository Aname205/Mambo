import discord
from discord.ext import commands
import asyncio

class Heal(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def heal(self, ctx):
        player = await self.bot.db.players.get_player(ctx.author.id)
        if not player:
            return await ctx.send("Player data not found.")

        max_health = player[2]
        current_health = player[23] if player[23] is not None else max_health

        if current_health >= max_health:
            return await ctx.send("❤️ You are already at **full health**!")

        missing_health = max_health - current_health
        
        # Calculate heal cost
        if max_health < 1000:
            # Simple formula for lower levels: 1 coin per 1 HP missing
            heal_cost = missing_health
        else:
            # Scaling formula for high HP players to prevent "infinite" effective HP
            base_cost = 1.0
            missing_ratio = missing_health / max_health
            # Cost increases quadratically based on how much % health is missing
            heal_cost = int(base_cost * (1 + (missing_ratio * 5) ** 2) * missing_health)

        wallet, _ = await self.bot.db.get_balance(ctx.author.id)

        # check if player has enough money
        if wallet < heal_cost:
            return await ctx.send(f"⚠️ **Insufficient Funds!**\nYou need **{heal_cost}** coins to heal, but you only have **{wallet}** coins.")

        # Process Healing immediately
        await self.bot.db.update_wallet(ctx.author.id, -heal_cost)
        await self.bot.db.players.update_current_health(ctx.author.id, max_health)

        embed = discord.Embed(
            title="❤️ Healing Complete",
            description=f"You have been fully healed to **{max_health} HP**.",
            color=discord.Color.green()
        )
        embed.add_field(name="Healed For", value=f"**+{missing_health} HP**", inline=True)
        embed.add_field(name="Cost", value=f"**{heal_cost}** 🪙", inline=True)
        embed.set_footer(text=f"Remaining Balance: {wallet - heal_cost} coins")

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Heal(bot))
