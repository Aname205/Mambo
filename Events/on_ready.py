from discord.ext import commands
from Database.database import Database

class OnReady(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.db = Database(bot)

    @commands.Cog.listener()
    async def on_ready(self):
        print("Mambo")
        await self.bot.db.connect()
        print("Database connected")
        await self.bot.db.ensure_fishing_pool()
        print("Fishing pool generated")

async def setup(bot):
    await bot.add_cog(OnReady(bot))