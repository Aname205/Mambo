from discord.ext import commands
from Database.database import Database

class OnReady(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.db = Database(bot)

    @commands.Cog.listener()
    async def on_ready(self):
        print("Mambo")
        try:
            await self.bot.db.connect()
            print("Database connected")
            await self.bot.db.ensure_fishing_pool()
            print("Fishing pool generated")
            await self.bot.db.ensure_equipments()
            print("Equipments generated")
            await self.bot.db.ensure_monsters()
            print("Monsters generated")
        except Exception as e:
            print(e)

async def setup(bot):
    await bot.add_cog(OnReady(bot))