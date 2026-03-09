import random
import asyncio
import discord
from discord.ext import commands

class HighLow(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.active_games = {}

    @commands.command()
    async def highlow(self, ctx):

        # Check active game
        if ctx.author.id in self.active_games:
            old_task = self.active_games[ctx.author.id]
            old_task.cancel()

        # Randomize numbers
        hidden_number = random.randint(1, 100)
        shown_number = random.randint(1, 100)

        # Create embed
        embed = discord.Embed(
            title= "📈Higher / Lower📉",
            description= f"{ctx.author.mention} started a new Higher/Lower game\n\n"
                         f"Higher or Lower than {shown_number}"
        )

        embed.add_field(
            name="React in 30s",
            value="⬆️ for Higher\n⬇️ for Lower",
            inline=False
        )

        message = await ctx.send(embed=embed)

        # Add emojis
        await message.add_reaction("⬆️")
        await message.add_reaction("⬇️")

        # Check reactions
        def check(reaction, user):
            return (
                    not user.bot
                    and user == ctx.author
                    and reaction.message.id == message.id
                    and str(reaction.emoji) in ["⬆️", "⬇️"]
            )

        task = asyncio.current_task()
        self.active_games[ctx.author.id] = task

        try:
            reaction, user = await self.bot.wait_for(
                "reaction_add", timeout=30.0, check=check
                )

        except asyncio.TimeoutError:
            embed.color = discord.Color.orange()
            embed.add_field(
                name="Result",
                value="⏰ Time ran out!",
                inline=False
            )
            await message.edit(embed=embed)
            await message.clear_reactions()

            self.active_games.pop(ctx.author.id, None)
            return
        except asyncio.CancelledError:
            self.active_games.pop(ctx.author.id, None)
            return

        guess = str(reaction.emoji)

        # Check results
        if guess == "⬆️":
            user_correct = hidden_number > shown_number
        else:
            user_correct = hidden_number < shown_number

        reward = 100

        if hidden_number == shown_number:
            result = f"🤯 It's a tie! The number was {hidden_number}"
            embed.color = discord.Color.gold()
        elif user_correct:
            result = (f"✅ Correct! The number was {hidden_number}\n"
                      f"You earned {reward} 🪙")
            embed.color = discord.Color.green()

            # Change balance
            await self.bot.db.update_wallet(ctx.author.id, reward)

        else:
            result = f"❌ Wrong! The number was {hidden_number}"
            embed.color = discord.Color.red()

        embed.add_field(
            name="Result",
            value=result,
            inline=False
        )

        # Edit embed and clear reactions
        await message.edit(embed=embed)
        await message.clear_reactions()

        # Remove active game
        self.active_games.pop(ctx.author.id, None)
        return

async def setup(bot):
    await bot.add_cog(HighLow(bot))