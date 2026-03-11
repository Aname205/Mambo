import random
import discord
import discord.ext.commands as commands
from flask import ctx

def build_board(guesses):
    board = ""

    for guess, result in guesses:
        board += f"{guess.upper()} {result}\n"

    return board

def check_guess(guess, word):
    result = ["⬛"] * 5
    word_letters = list(word)

    for i in range(5):
        if guess[i] == word[i]:
            result[i] = "🟩"
            word_letters[i] = None

    for i in range(5):
        if result[i] == "⬛" and guess[i] in word_letters:
            result[i] = "🟨"
            word_letters[word_letters.index(guess[i])] = None

    return "".join(result)

class Wordle(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_games = {}

        with open("../wordle.txt") as f:
            self.words = [w.strip() for w in f.readlines()]

    @commands.command()
    async def wordle(self, ctx):
        user_id = ctx.author.id

        if user_id in self.active_games:
            await ctx.send("You are already in a Wordle game!")
            return

        word = random.choice(self.words)

        self.active_games[user_id] = {
            "word": word,
            "attempts": 0,
            "guesses": [],
        }

        embed = discord.Embed(
            title="Wordle",
            description="Guess the **5 letter word**.\nYou have **6 attempts**.",
            color=discord.Color.green()
        )

        embed.add_field(
            name="Board",
            value="No guesses yet",
            inline=False
        )

        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):

        if message.author.bot:
            return

        ctx = await self.bot.get_context(message)
        if ctx.valid:
            return

        user_id = message.author.id

        if user_id not in self.active_games:
            return

        guess = message.content.lower()

        if len(guess) != 5:
            return

        game = self.active_games[user_id]
        word = game["word"]

        result = check_guess(guess, word)

        game["attempts"] += 1
        game["guesses"].append((guess, result))

        board = build_board(game["guesses"])

        # await message.channel.send(f"{guess.upper()}:\n {result}")

        embed = discord.Embed(
            title="Wordle",
            description=f"Guessed **{game['attempts']}/6** attempts.",
            color=discord.Color.green()
        )

        embed.add_field(
            name="Board",
            value= f"```{board}```",
            inline=False
        )

        await message.channel.send(embed=embed)

        if guess == word:
            await message.channel.send("You win!")
            del self.active_games[user_id]
            return

        if game["attempts"] >= 6:
            await message.channel.send(f"You lose :(\n The word was **{word}**")
            del self.active_games[user_id]


async def setup(bot):
    await bot.add_cog(Wordle(bot))