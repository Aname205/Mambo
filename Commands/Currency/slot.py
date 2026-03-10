import discord
import random
from discord.ext import commands


class Slot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # slot symbols
        self.symbols = [
            "🍒",
            "🍋",
            "🍉",
            "🍇",
            "⭐",
            "💎"
        ]

    @commands.command("")
    async def slot(self, ctx, bet=None):
        wallet, bank = await self.bot.db.get_balance(ctx.author.id)

        if bet is None:
            return await ctx.send("You must specify a bet amount")

        if str(bet) == "all":
            bet = wallet
        else:
            try:
                bet = int(bet)
            except ValueError:
                return await ctx.send("Please enter a valid number")

        if bet < 50:
            return await ctx.send("Minimum bet is **50 coins**")

        if wallet < bet:
            return await ctx.send("You don't have enough money")

        # spin slots
        top_row = [random.choice(self.symbols) for _ in range(3)]
        mid_row = [random.choice(self.symbols) for _ in range(3)]
        bot_row = [random.choice(self.symbols) for _ in range(3)]

        top_display = " | ".join(top_row)
        mid_display = " | ".join(mid_row)
        bot_display = " | ".join(bot_row)

        multiplier = 0
        outcome = ""

        if mid_row[0] == mid_row[1] == mid_row[2]:
            multiplier = 2
            outcome = "💎 JACKPOT!"

        elif mid_row[0] == mid_row[1] or mid_row[1] == mid_row[2] or mid_row[0] == mid_row[2]:
            multiplier = 1.5
            outcome = "✨ Two matched!"

        else:
            multiplier = -1
            outcome = "🥀 You lost"

        if multiplier > 0:
            winnings = bet * multiplier
            await self.bot.db.update_wallet(ctx.author.id, winnings)
            result_text = f"🎊 You win **{winnings:,} coins!**"
            color = discord.Color.green()

        else:
            await self.bot.db.update_wallet(ctx.author.id, -bet)
            result_text = f"🥀 You lose **{bet:,} coins!**"
            color = discord.Color.red()

        embed = discord.Embed(
            title="🎰 Slot Machine",
            color=color
        )

        embed.add_field(
            name="Spin Result",
            value=f"{top_display}\n**{mid_display}  <---**\n{bot_display}",
            inline=False
        )

        embed.add_field(
            name="Outcome",
            value=f"{outcome}\n{result_text}",
            inline=False
        )

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Slot(bot))