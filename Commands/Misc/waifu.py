import discord
import aiohttp
from discord.ext import commands


async def fetch_waifu():
    """Fetch a random waifu image URL from waifu.pics API."""
    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.waifu.pics/sfw/waifu") as resp:
            if resp.status != 200:
                return None
            data = await resp.json()
            return data.get("url")


class Waifu(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="waifu")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def waifu(self, ctx):
        """Send a random waifu image."""
        url = await fetch_waifu()

        if not url:
            return await ctx.send("❌ Could not fetch a waifu image. Try again later!")

        em = discord.Embed(color=discord.Color.pink())
        em.set_author(name=f"{ctx.author.name}", icon_url=ctx.author.display_avatar.url)
        em.set_image(url=url)
        em.set_footer(text="Src: waifu.pics")

        await ctx.send(embed=em)

    @waifu.error
    async def waifu_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"Try again in **{error.retry_after:.1f}s**.")


async def setup(bot):
    await bot.add_cog(Waifu(bot))

