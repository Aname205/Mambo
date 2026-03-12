import discord
import random
import asyncio
from discord.ext import commands

# --- UI COMPONENTS ---
class RPSButtons(discord.ui.View):
    def __init__(self, ctx, bet, bot, active_games):
        super().__init__(timeout=15)
        self.ctx = ctx
        self.bet = bet
        self.bot = bot
        self.active_games = active_games
        self.choice = None

    async def on_timeout(self):
        # Automatically remove from active games list on timeout
        self.active_games.discard(self.ctx.author.id)

    async def process_game(self, interaction: discord.Interaction, player_choice):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message("This is not your game!", ephemeral=True)

        self.choice = player_choice
        self.stop() # Stop the view to return result to the main function
        await interaction.response.defer()

    @discord.ui.button(label="Rock", style=discord.ButtonStyle.gray, emoji="✊")
    async def rock(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_game(interaction, "✊")

    @discord.ui.button(label="Paper", style=discord.ButtonStyle.gray, emoji="✋")
    async def paper(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_game(interaction, "✋")

    @discord.ui.button(label="Scissors", style=discord.ButtonStyle.gray, emoji="✌️")
    async def scissors(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_game(interaction, "✌️")

# --- COG ---
class RPS(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_games = set()

    @commands.command(name="rps")
    async def rps(self, ctx, bet=None):
        wallet, bank = await self.bot.db.get_balance(ctx.author.id)

        if bet is None:
            return await ctx.send("❌ You must specify a bet amount!")

        if str(bet) == "all":
            bet = wallet
        else:
            try:
                bet = int(bet)
            except ValueError:
                return await ctx.send("❌ Please enter a valid number!")

        if bet < 50:
            return await ctx.send("❌ Minimum bet is **50 coins**")

        if wallet < bet:
            return await ctx.send("❌ You don't have enough money!")

        if ctx.author.id in self.active_games:
            return await ctx.send("⚠️ You are already playing a game!")

        self.active_games.add(ctx.author.id)

        try:
            em = discord.Embed(
                title="✊ Rock Paper Scissors",
                description=f"{ctx.author.mention} bet **{bet:,} coins**\n\nChoose your move by clicking the buttons below:",
                color=discord.Color.light_grey()
            )

            view = RPSButtons(ctx, bet, self.bot, self.active_games)
            msg = await ctx.send(embed=em, view=view)

            # Wait for user to press a button
            await view.wait()

            if view.choice is None:
                await msg.edit(embed=discord.Embed(
                    title="⌛ Game timed out",
                    description="You didn't make a move in time.",
                    color=discord.Color.orange()
                ), view=None)
                return

            player_choice = view.choice
            reactions = ["✊", "✋", "✌️"]
            bot_choice = random.choice(reactions)

            choice_map = {
                "✊": "✊ Rock",
                "✋": "✋ Paper",
                "✌️": "✌️ Scissors"
            }

            # Determine win/lose logic
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

            # Process result and reward
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

            final_em = discord.Embed(
                title="✊ Rock Paper Scissors",
                color=color
            )
            final_em.add_field(name=ctx.author.display_name, value=choice_map[player_choice], inline=True)
            final_em.add_field(name="Bot", value=choice_map[bot_choice], inline=True)
            final_em.add_field(name="Result", value=text, inline=False)

            await msg.edit(embed=final_em, view=None)

        finally:
            self.active_games.discard(ctx.author.id)

async def setup(bot):
    await bot.add_cog(RPS(bot))