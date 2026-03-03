import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import asyncio
import aiosqlite
import os
from keep_alive import keep_alive

load_dotenv()
token = os.getenv("DISCORD_TOKEN")

keep_alive()

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='m', intents=intents)

@bot.event
async def on_ready():
    print("Mambo")
    bot.db = await aiosqlite.connect("MyBank.db")
    await asyncio.sleep(5)
    async with bot.db.cursor() as cursor:
        await cursor.execute("""CREATE TABLE IF NOT EXISTS Mambo(
            wallet INTEGER,
            bank INTEGER,
            user INTEGER)"""
        )
    await bot.db.commit()
    print("Database created")

async def create_balance(user):
    async with bot.db.cursor() as cursor:
        await cursor.execute("""INSERT INTO Mambo(wallet, bank, user) VALUES(?, ?, ?)""", (100, 0, user.id))
    await bot.db.commit()

async def get_balance(user):
    async with bot.db.cursor() as cursor:
        await cursor.execute("""SELECT wallet, bank FROM Mambo WHERE user = ?""", (user.id,))
        data = await cursor.fetchone()

    if data is None:
        await create_balance(user)
        return 100, 0

    wallet, bank = data
    return wallet, bank

@bot.command()
async def balance(ctx):
    wallet, bank = await get_balance(ctx.author)
    em = discord.Embed(
        title=f"{ctx.author.name}'s Balance",
        color=discord.Color.blue(),
    )
    em.add_field(name="Wallet", value=wallet)
    em.add_field(name="Bank", value=bank)
    await ctx.send(embed=em)

@bot.command()
async def mambo(ctx):
    await ctx.send(f"{ctx.author.mention} Mambo")

bot.run(token, log_handler=handler, log_level=logging.DEBUG)
