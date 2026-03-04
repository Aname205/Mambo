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

handler = logging.FileHandler(filename='../discord.log', encoding='utf-8', mode='w')

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='m', intents=intents)

async def main():
    async with bot:
        await bot.load_extension("events")
        await bot.load_extension("commands")
        await bot.start(token)

asyncio.run(main())

