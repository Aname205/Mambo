from discord.ext import commands
from database import Database

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.db = Database(bot)

    @commands.Cog.listener()
    async def on_ready(self):
        print("Mambo")
        await self.bot.db.connect()
        print("Database connected & tables ready")

async def setup(bot):
    await bot.add_cog(Events(bot))