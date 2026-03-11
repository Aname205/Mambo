import random
import discord
import discord.ext.commands as commands

async def check_guess(guess, word):
    result = ["⬛"] * 5
    word_letters = list(word)

    for i in range(5):
        if guess[i] == word[i]:
            result = ["🟩"]
            word_letters[i] = None

    for i in range(5):
        if (guess[i] in word_letters) and result[i] == "⬛":
            result[i] = ["🟨"]
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

        self.active_games = {
            "wordle": word,
            "attempts": 0
        }

        await ctx.send(
            "🟩 **Wordle Started!**\n"
            "Guess the **5 letter word**.\n"
            "You have **6 attempts**.\n"
            "Send guesses directly in chat."
        )


async def setup(bot):
    await bot.add_cog(Wordle(bot))