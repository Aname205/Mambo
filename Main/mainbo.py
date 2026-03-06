import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import asyncio
import os
import sys
from Main.keep_alive import keep_alive

load_dotenv()
token = os.getenv("DISCORD_TOKEN")


handler = logging.FileHandler(filename='../discord.log', encoding='utf-8', mode='w')

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix=('m', 'M'), intents=intents, case_insensitive=True, help_command=None)

async def main():
    async with bot:
        keep_alive()
        await bot.load_extension("Events.on_ready")
        await bot.load_extension("Commands.Currency.balance")
        await bot.load_extension("Commands.Currency.blackjack")
        await bot.load_extension("Commands.Currency.inventory")
        await bot.load_extension("Commands.Currency.items")
        await bot.load_extension("Commands.Currency.fish")
        await bot.load_extension("Commands.Misc.mambo")
        await bot.load_extension("Commands.Misc.mmb")
        await bot.load_extension("Commands.Misc.help")
        await bot.start(token)

asyncio.run(main())
