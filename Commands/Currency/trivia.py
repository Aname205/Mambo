import discord
import aiohttp
import html
import random
from discord.ext import commands

# Category mapping: friendly name -> OpenTDB category ID
CATEGORIES = {
    "general": 9,
    "books": 10,
    "film": 11,
    "music": 12,
    "theatre": 13,
    "tv": 14,
    "videogames": 15,
    "boardgames": 16,
    "science": 17,
    "computers": 18,
    "math": 19,
    "mythology": 20,
    "sports": 21,
    "geography": 22,
    "history": 23,
    "politics": 24,
    "art": 25,
    "celebrities": 26,
    "animals": 27,
    "vehicles": 28,
    "comics": 29,
    "gadgets": 30,
    "anime": 31,
    "cartoons": 32,
}

# Reward coins based on difficulty
DIFFICULTY_REWARDS = {
    "easy": 50,
    "medium": 100,
    "hard": 200,
}

DIFFICULTY_EMOJI = {
    "easy": "🟢",
    "medium": "🟡",
    "hard": "🔴",
}

ANSWER_LABELS = ["A", "B", "C", "D"]


# ============ API HELPER ============

async def fetch_trivia(category_id=None, difficulty=None):
    """Fetch a single multiple-choice trivia question from OpenTDB API."""
    # Build API URL with optional filters
    url = "https://opentdb.com/api.php?amount=1&type=multiple"
    if category_id:
        url += f"&category={category_id}"
    if difficulty:
        url += f"&difficulty={difficulty}"

    # Make async HTTP request
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()

    # response_code 0 = success, anything else = error/no results
    if data["response_code"] != 0 or not data["results"]:
        return None

    result = data["results"][0]
    # Decode HTML entities (API returns HTML-encoded strings like &amp;)
    question = html.unescape(result["question"])
    correct = html.unescape(result["correct_answer"])
    incorrect = [html.unescape(a) for a in result["incorrect_answers"]]
    category = html.unescape(result["category"])
    difficulty = result["difficulty"]

    # Shuffle answers
    answers = incorrect + [correct]
    random.shuffle(answers)
    correct_index = answers.index(correct)

    return {
        "question": question,
        "answers": answers,
        "correct_index": correct_index,
        "correct_answer": correct,
        "category": category,
        "difficulty": difficulty,
    }


# ============ UI COMPONENTS ============

class TriviaAnswerButton(discord.ui.Button):
    def __init__(self, label, index, view_ref):
        style = discord.ButtonStyle.secondary
        super().__init__(label=label, style=style)
        self.index = index
        self.view_ref = view_ref

    async def callback(self, interaction: discord.Interaction):
        view: TriviaView = self.view_ref

        # Only the player who started can answer
        if interaction.user != view.ctx.author:
            return await interaction.response.defer()

        if view.answered:
            return await interaction.response.defer()

        view.answered = True
        view.stop()

        correct = self.index == view.correct_index
        reward = DIFFICULTY_REWARDS.get(view.difficulty, 50)

        # Color all buttons to show correct/wrong
        for child in view.children:
            if isinstance(child, TriviaAnswerButton):
                child.disabled = True
                if child.index == view.correct_index:
                    child.style = discord.ButtonStyle.success  # Green for correct
                elif child.index == self.index and not correct:
                    child.style = discord.ButtonStyle.danger  # Red for wrong pick

        # Correct: reward coins and show green embed
        if correct:
            await self.view_ref.bot.db.update_wallet(interaction.user.id, reward)
            em = view.build_embed(
                result_text=f"✅ Correct! You earned **{reward:,} :coin:**",
                color=discord.Color.green()
            )
        # Wrong: show red embed with the correct answer
        else:
            em = view.build_embed(
                result_text=f"❌ Wrong! The correct answer was **{view.correct_answer}**",
                color=discord.Color.red()
            )

        await interaction.response.edit_message(embed=em, view=view)


class TriviaView(discord.ui.View):
    def __init__(self, bot, ctx, trivia_data):
        super().__init__(timeout=30)
        self.bot = bot
        self.ctx = ctx
        self.answered = False
        self.message = None

        self.question = trivia_data["question"]
        self.answers = trivia_data["answers"]
        self.correct_index = trivia_data["correct_index"]
        self.correct_answer = trivia_data["correct_answer"]
        self.category = trivia_data["category"]
        self.difficulty = trivia_data["difficulty"]

        # Create answer buttons
        for i, answer in enumerate(self.answers):
            label = f"{ANSWER_LABELS[i]}. {answer}"
            # Truncate label if too long (Discord limit: 80 chars)
            if len(label) > 80:
                label = label[:77] + "..."
            self.add_item(TriviaAnswerButton(label=label, index=i, view_ref=self))

    def build_embed(self, result_text=None, color=None):
        diff_emoji = DIFFICULTY_EMOJI.get(self.difficulty, "⚪")
        reward = DIFFICULTY_REWARDS.get(self.difficulty, 50)

        if color is None:
            color = discord.Color.blurple()

        em = discord.Embed(
            title="🧠 Trivia Time!",
            color=color
        )
        em.add_field(
            name="",
            value=f"**{self.question}**",
            inline=False
        )
        em.add_field(
            name="Category",
            value=self.category,
            inline=True
        )
        em.add_field(
            name="Difficulty",
            value=f"{diff_emoji} {self.difficulty.capitalize()}",
            inline=True
        )
        em.add_field(
            name="Reward",
            value=f"{reward:,} :coin:",
            inline=True
        )

        if result_text:
            em.add_field(name="", value=result_text, inline=False)

        em.set_footer(text=f"Requested by {self.ctx.author.name}", icon_url=self.ctx.author.display_avatar.url)

        return em

    async def on_timeout(self):
        if self.answered:
            return

        self.answered = True

        # Disable all buttons and highlight correct answer
        for child in self.children:
            if isinstance(child, TriviaAnswerButton):
                child.disabled = True
                if child.index == self.correct_index:
                    child.style = discord.ButtonStyle.success

        em = self.build_embed(
            result_text=f"⌛ Time's up! The correct answer was **{self.correct_answer}**",
            color=discord.Color.dark_grey()
        )

        if self.message:
            try:
                await self.message.edit(embed=em, view=self)
            except discord.HTTPException:
                pass


class Trivia(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="trivia", aliases=["tv"])
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def trivia(self, ctx, difficulty: str = None, category: str = None):
        # Validate difficulty
        if difficulty:
            difficulty = difficulty.lower()
            if difficulty not in DIFFICULTY_REWARDS:
                return await ctx.send("Difficulty must be `easy`, `medium`, or `hard`.")

        # Resolve category
        category_id = None
        if category:
            category_lower = category.lower()
            if category_lower in CATEGORIES:
                category_id = CATEGORIES[category_lower]
            else:
                # Show available categories
                cat_list = ", ".join(f"`{c}`" for c in sorted(CATEGORIES.keys()))
                return await ctx.send(
                    f"Unknown category **{category}**.\n"
                    f"Available: {cat_list}"
                )


        # Fetch question from API
        trivia_data = await fetch_trivia(category_id, difficulty)
        if not trivia_data:
            return await ctx.send("❌ Could not fetch a trivia question. Try again later!")

        # Create and send the trivia view
        view = TriviaView(self.bot, ctx, trivia_data)
        view.message = await ctx.send(embed=view.build_embed(), view=view)

    @trivia.error
    async def trivia_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"Try again in **{error.retry_after:.1f}s**.")

    @commands.command(name="triviacategories", aliases=["tvc"])
    async def trivia_categories(self, ctx):
        """Show all available trivia categories."""
        em = discord.Embed(title="🧠 Trivia Categories", color=discord.Color.blurple())

        cat_text = ""
        for name, cat_id in sorted(CATEGORIES.items(), key=lambda x: x[1]):
            emoji = "📚" if cat_id <= 13 else "🎮" if cat_id <= 16 else "🔬" if cat_id <= 19 else "🌍" if cat_id <= 23 else "🎨" if cat_id <= 26 else "🐾" if cat_id <= 28 else "📺"
            cat_text += f"{emoji} `{name}`\n"

        em.description = cat_text
        em.set_footer(text="Usage: mtrivia <category> [difficulty]")

        await ctx.send(embed=em)


async def setup(bot):
    await bot.add_cog(Trivia(bot))


