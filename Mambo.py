import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
from keep_alive import keep_alive

load_dotenv()
token = os.getenv("DISCORD_TOKEN")

keep_alive()

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.members = True
intents.messages = True

bot = commands.Bot(command_prefix='m', intents=intents)

@bot.event
async def on_ready():
    print("Mambo")

@bot.command()
async def mambo(ctx):
    await ctx.send(f"{ctx.author.mention} Mambo")

@bot.command()
async def anngu(ctx):
    await ctx.send("Tung An pha gia chi tu")

bot.run(token, log_handler=handler, log_level=logging.DEBUG)