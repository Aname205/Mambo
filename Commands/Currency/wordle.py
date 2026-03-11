import random
import discord
import discord.ext.commands as commands

def build_board(guesses):
    rows = []

    for guess, result in guesses:
        rows.append(f"{guess.upper()} {result}")

    while len(rows) < 6:
        rows.append("_____ ⬛⬛⬛⬛⬛")

    return ("\n".join(rows))

def update_letters(letter_map, guess, result):
    for i in range(5):
        letter = guess[i]
        color = result[i]

        if letter not in letter_map:
            letter_map[letter] = color
        else:
            if color == "🟩":
                letter_map[letter] = "🟩"
            elif color == "🟨" and letter_map[letter] == "⬛":
                letter_map[letter] = "🟨"

def letter_display(letter_map):
    correct = []
    misplaced = []
    wrong = []

    for letter, color in letter_map.items():
        if color == "🟩":
            correct.append(letter.upper())
        elif color == "🟨":
            misplaced.append(letter.upper())
        elif color == "⬛":
            wrong.append(letter.upper())

    text = ""

    if correct:
        text += "🟩 " + " ".join(correct) + "\n"
    if misplaced:
        text += "🟨 " + " ".join(misplaced) + "\n"
    if wrong:
        text += "⬛ " + " ".join(wrong) + "\n"

    return text if text else "No letters guessed yet!"

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

        embed = discord.Embed(
            title="Wordle",
            description="Guess the **5 letter word**.\nYou have **6 attempts**.",
            color=discord.Color.green()
        )

        empty_board = build_board([])

        embed.add_field(
            name="Board",
            value=f"```{empty_board}```",
            inline=False
        )

        game_message = await ctx.send(embed=embed)

        self.active_games[user_id] = {
            "word": word,
            "attempts": 0,
            "guesses": [],
            "letters": {},
            "message": game_message
        }

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

        guess = message.content.lower().strip()

        if len(guess) != 5 or not guess.isalpha():
            return

        game = self.active_games[user_id]
        word = game["word"]

        result = check_guess(guess, word)
        update_letters(game["letters"], guess, result)

        game["attempts"] += 1
        game["guesses"].append((guess, result))

        board = build_board(game["guesses"])
        letters = letter_display(game["letters"])

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

        embed.add_field(
            name="Letters",
            value=letters,
            inline=False
        )

        game_message = game["message"]
        await game_message.edit(embed=embed)

        if guess == word:
            await message.channel.send("You win!")
            del self.active_games[user_id]
            return

        if game["attempts"] >= 6:
            await message.channel.send(f"You lose :(\n The word was **{word}**")
            del self.active_games[user_id]

async def setup(bot):
    await bot.add_cog(Wordle(bot))