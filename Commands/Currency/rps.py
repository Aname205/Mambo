import discord
import random
import asyncio
from discord.ext import commands

class RPS(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_games = set()

    @commands.command("")
    async def rps(self, ctx, bet=None):
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

        if ctx.author.id in self.active_games:
            return await ctx.send("You are already playing a game!")

        self.active_games.add(ctx.author.id)

        try:
            em = discord.Embed(
                title="✊ Rock Paper Scissors",
                description=f"{ctx.author.mention} bet **{bet:,} coins**\n\nChoose your move:",
                color=discord.Color.light_grey()
            )

            em.add_field(
                name="Options",
                value="✊ Rock\n✋ Paper\n✌️ Scissors",
                inline=False
            )

            msg = await ctx.send(embed=em)

            reactions = ["✊", "✋", "✌️"]
            for r in reactions:
                await msg.add_reaction(r)

            def check(reaction, user):
                return (
                    user == ctx.author
                    and str(reaction.emoji) in reactions
                    and reaction.message.id == msg.id
                )

            try:
                reaction, user = await self.bot.wait_for(
                    "reaction_add",
                    timeout=15,
                    check=check
                )
            except asyncio.TimeoutError:
                await msg.edit(embed=discord.Embed(
                    title="⌛ Game timed out",
                    color=discord.Color.orange()
                ))
                return

            player_choice = str(reaction.emoji)

            bot_choice = random.choice(reactions)

            choice_map = {
                "✊": "✊ Rock",
                "✋": "✋ Paper",
                "✌️": "✌️ Scissors"
            }

            result = None

            if player_choice == bot_choice:
                result = "tie"

            elif (
                (player_choice == "✊" and bot_choice == "✌️") or
                (player_choice == "✋" and bot_choice == "✊") or
                (player_choice == "✌️" and bot_choice == "✋")
            ):
                result = "win"

            else:
                result = "lose"

            if result == "win":
                await self.bot.db.update_wallet(ctx.author.id, bet)
                text = f"🎊 You win **{bet:,} coins!**"
                color = discord.Color.green()

            elif result == "lose":
                await self.bot.db.update_wallet(ctx.author.id, -bet)
                text = f"🥀 You lose **{bet:,} coins!**"
                color = discord.Color.red()

            else:
                text = "🤝 It's a tie!"
                color = discord.Color.light_grey()

            em = discord.Embed(
                title="✊ Rock Paper Scissors",
                color=color
            )

            em.add_field(
                name=ctx.author.display_name,
                value=choice_map[player_choice],
                inline=True
            )

            em.add_field(
                name="Bot",
                value=choice_map[bot_choice],
                inline=True
            )

            em.add_field(
                name="Result",
                value=text,
                inline=False
            )

            await msg.edit(embed=em)

        finally:
            self.active_games.discard(ctx.author.id)


async def setup(bot):
    await bot.add_cog(RPS(bot))