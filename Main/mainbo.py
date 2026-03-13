import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import asyncio
import os
import sys
from keep_alive import keep_alive

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

load_dotenv()
token = os.getenv("DISCORD_TOKEN")


handler = logging.FileHandler(filename='../discord.log', encoding='utf-8', mode='w')

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.guilds = True
intents.reactions = True

bot = commands.Bot(command_prefix=('m', 'M'), intents=intents, case_insensitive=True, help_command=None)


async def start_bot_with_retry(max_retries=8, base_delay=5):
    delay = base_delay

    for attempt in range(1, max_retries + 1):
        try:
            await bot.start(token)
            return
        except discord.DiscordServerError as e:
            if attempt == max_retries:
                raise
            print(f"[DiscordServerError] attempt {attempt}/{max_retries}: {e}. Retrying in {delay}s...")
            await asyncio.sleep(delay)
            delay = min(delay * 2, 60)
        except discord.HTTPException as e:
            # Retry only transient HTTP 5xx errors.
            if 500 <= getattr(e, "status", 0) < 600 and attempt < max_retries:
                print(f"[HTTP {e.status}] attempt {attempt}/{max_retries}: {e}. Retrying in {delay}s...")
                await asyncio.sleep(delay)
                delay = min(delay * 2, 60)
            else:
                raise


async def main():
    print(f"Starting Mambo bot (PID {os.getpid()})")
    async with bot:
        keep_alive()
        await bot.load_extension("Events.on_ready")
        await bot.load_extension("Commands.Currency.balance")
        await bot.load_extension("Commands.Currency.blackjack")
        await bot.load_extension("Commands.Currency.daily")
        await bot.load_extension("Commands.Currency.inventory")
        await bot.load_extension("Commands.Currency.items")
        await bot.load_extension("Commands.Currency.fish")
        await bot.load_extension("Commands.Currency.trivia")
        await bot.load_extension("Commands.Misc.mambo")
        await bot.load_extension("Commands.Misc.mmb")
        await bot.load_extension("Commands.Misc.help")
        await bot.load_extension("Commands.Misc.waifu")
        await bot.load_extension("Commands.Currency.highlow")
        await bot.load_extension("Commands.Currency.rps")
        await bot.load_extension("Commands.Currency.market")
        await bot.load_extension("Commands.Currency.lottery")
        await bot.load_extension("Commands.Currency.slot")
        await bot.load_extension("Commands.Currency.poker")
        await bot.load_extension("Commands.Currency.status")
        await bot.load_extension("Commands.Currency.wordle")
        await bot.load_extension("Commands.Currency.duel")
        await bot.load_extension("Commands.Currency.hunt")
        await bot.load_extension("Commands.Currency.dungeon")
        await start_bot_with_retry()

asyncio.run(main())
