import discord
import random
from datetime import datetime, timedelta, timezone
from discord.ext import commands, tasks

# ============ CONFIGURATION ============
ENROL_PRICE = 100           # Ticket price per entry
INTERVAL_MINUTES = 20        # Auto-draw every N minutes
NUMBER_RANGE = (1, 100)     # Players pick a number in this range
ANNOUNCEMENT_CHANNEL = "lottery-notice-test"  # Fixed channel name for draw results


class Lottery(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_announcement_channel(self):
        """Find the announcement channel by name across all guilds."""
        for guild in self.bot.guilds:
            channel = discord.utils.get(guild.text_channels, name=ANNOUNCEMENT_CHANNEL)
            if channel:
                return channel
        return None

    async def cog_load(self):
        """Start the background loop when the cog is loaded."""
        self.lottery_loop.start()

    async def cog_unload(self):
        """Stop the background loop when the cog is unloaded."""
        self.lottery_loop.cancel()

    # ============ HELPERS ============

    async def ensure_active_lottery(self):
        """Make sure there is an active lottery session. Create one if not."""
        lottery = await self.bot.db.get_active_lottery()
        if lottery is None:
            now = datetime.now(timezone.utc)
            end = now + timedelta(minutes=INTERVAL_MINUTES)
            await self.bot.db.create_lottery(ENROL_PRICE, 0, now.isoformat(), end.isoformat())

    async def perform_draw(self):
        """Draw the winning number, reward winners, and create a new session."""
        lottery = await self.bot.db.get_active_lottery()
        if lottery is None:
            return None

        lottery_id, enrol_price, total_price, _, start_date, end_date = lottery

        # Pick winning number
        winning_number = random.randint(*NUMBER_RANGE)
        await self.bot.db.set_winning_number(lottery_id, winning_number)

        # Find winners
        winners = await self.bot.db.get_lottery_winners(lottery_id, winning_number)
        player_count = await self.bot.db.count_lottery_players(lottery_id)

        rollover = 0
        winner_payout = 0
        winner_ids = []

        if winners and total_price > 0:
            winner_payout = total_price // len(winners)
            # Remainder stays in the prize pool for the next round
            rollover = total_price - (winner_payout * len(winners))
            for w in winners:
                # w = (id, user_id, lottery_id, bet_number)
                await self.bot.db.update_wallet(w[1], winner_payout)
                winner_ids.append(w[1])
        else:
            # No winners — jackpot rolls over
            rollover = total_price

        # Create a new session immediately
        now = datetime.now(timezone.utc)
        end = now + timedelta(minutes=INTERVAL_MINUTES)
        await self.bot.db.create_lottery(ENROL_PRICE, rollover, now.isoformat(), end.isoformat())

        return {
            "lottery_id": lottery_id,
            "winning_number": winning_number,
            "total_price": total_price,
            "player_count": player_count,
            "winners": winner_ids,
            "winner_payout": winner_payout,
            "rollover": rollover,
        }

    def format_remaining(self, end_date_str):
        """Return a human-readable time remaining string."""
        end = datetime.fromisoformat(end_date_str)
        if end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)
        remaining = end - datetime.now(timezone.utc)

        if remaining.total_seconds() <= 0:
            return "Drawing soon..."

        total_secs = int(remaining.total_seconds())
        hours = total_secs // 3600
        minutes = (total_secs % 3600) // 60
        secs = total_secs % 60

        parts = []
        if hours:
            parts.append(f"{hours}h")
        if minutes:
            parts.append(f"{minutes}m")
        parts.append(f"{secs}s")
        return " ".join(parts)

    # ============ BACKGROUND TASK ============

    @tasks.loop(seconds=30)
    async def lottery_loop(self):
        """Check every 30s if the active lottery has expired, then auto-draw."""
        # Skip if database is not ready yet
        if not hasattr(self.bot, 'db') or self.bot.db is None or self.bot.db.db is None:
            return

        try:
            await self.ensure_active_lottery()

            lottery = await self.bot.db.get_active_lottery()
            if lottery is None:
                return

            _, _, _, _, _, end_date = lottery
            end = datetime.fromisoformat(end_date)
            if end.tzinfo is None:
                end = end.replace(tzinfo=timezone.utc)

            if datetime.now(timezone.utc) < end:
                return  # Not yet time

            # Time to draw
            result = await self.perform_draw()
            if result is None:
                return

            # Announce in the fixed channel
            channel = self.get_announcement_channel()
            if channel:
                em = discord.Embed(title="🎰 Lottery Draw Results!", color=discord.Color.gold())
                em.add_field(name="🎯 Winning Number", value=f"**{result['winning_number']}**", inline=True)
                em.add_field(name="👥 Participants", value=f"{result['player_count']}", inline=True)
                em.add_field(name="💰 Prize Pool", value=f"{result['total_price']:,} :coin:", inline=True)

                if result["winners"]:
                    mentions = ", ".join(f"<@{uid}>" for uid in result["winners"])
                    em.add_field(
                        name="🎊 Winners!",
                        value=f"{mentions}\nEach won **{result['winner_payout']:,} :coin:**",
                        inline=False
                    )
                else:
                    em.add_field(
                        name="😢 No Winners",
                        value=f"Jackpot of **{result['rollover']:,} :coin:** rolls over to the next round!",
                        inline=False
                    )

                em.add_field(
                    name="🆕 Next Round",
                    value=f"A new lottery has started! Buy a ticket with `mlottery buy <number>`",
                    inline=False
                )

                await channel.send(embed=em)
        except Exception as e:
            print(f"[Lottery Loop Error] {e}")

    @lottery_loop.before_loop
    async def before_lottery_loop(self):
        """Wait until the bot is ready before starting the loop."""
        await self.bot.wait_until_ready()

    # ============ COMMANDS ============

    @commands.group(name="lottery", aliases=["lotto"], invoke_without_command=True)
    async def lottery(self, ctx):
        """Show current lottery session info."""

        await self.ensure_active_lottery()
        lotto = await self.bot.db.get_active_lottery()

        if lotto is None:
            return await ctx.send("❌ No active lottery session.")

        lottery_id, enrol_price, total_price, _, start_date, end_date = lotto
        player_count = await self.bot.db.count_lottery_players(lottery_id)
        remaining = self.format_remaining(end_date)

        em = discord.Embed(title="🎰 Lottery", color=discord.Color.gold())
        em.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
        em.add_field(name="🎟️ Ticket Price", value=f"{enrol_price:,} :coin:", inline=True)
        em.add_field(name="💰 Prize Pool", value=f"{total_price:,} :coin:", inline=True)
        em.add_field(name="👥 Participants", value=f"{player_count}", inline=True)
        em.add_field(name="⏰ Time Remaining", value=remaining, inline=True)
        em.add_field(name="🔢 Number Range", value=f"{NUMBER_RANGE[0]} – {NUMBER_RANGE[1]}", inline=True)
        em.set_footer(text="Use: mlottery buy <number> to enter!")

        # Check if this user already has a ticket
        entry = await self.bot.db.get_lottery_player_entry(ctx.author.id, lottery_id)
        if entry:
            em.add_field(name="🎫 Your Ticket", value=f"Number **{entry[3]}**", inline=False)

        await ctx.send(embed=em)

    @lottery.command(name="buy")
    async def lottery_buy(self, ctx, number: int = None):
        """Buy a lottery ticket by picking a number."""
        if number is None:
            return await ctx.send(f"Please pick a number between {NUMBER_RANGE[0]} and {NUMBER_RANGE[1]}.")

        if number < NUMBER_RANGE[0] or number > NUMBER_RANGE[1]:
            return await ctx.send(f"Number must be between {NUMBER_RANGE[0]} and {NUMBER_RANGE[1]}.")

        await self.ensure_active_lottery()
        lotto = await self.bot.db.get_active_lottery()

        if lotto is None:
            return await ctx.send("❌ No active lottery session.")

        lottery_id, enrol_price, _, _, _, _ = lotto

        # Check if user already entered
        entry = await self.bot.db.get_lottery_player_entry(ctx.author.id, lottery_id)
        if entry:
            return await ctx.send(f"You already have a ticket with number **{entry[3]}**. One ticket per round!")

        # Check wallet
        wallet, _ = await self.bot.db.get_balance(ctx.author.id)
        if wallet < enrol_price:
            return await ctx.send(f"You need at least **{enrol_price:,} :coin:** to buy a ticket.")

        # Deduct money and register
        await self.bot.db.update_wallet(ctx.author.id, -enrol_price)
        await self.bot.db.add_lottery_player(ctx.author.id, lottery_id, number)
        await self.bot.db.update_total_price(lottery_id, enrol_price)


        em = discord.Embed(title="🎟️ Ticket Purchased!", color=discord.Color.green())
        em.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
        em.description = (
            f"You picked number **{number}**\n"
            f"Paid **{enrol_price:,} :coin:**\n\n"
            f"Good luck! 🍀"
        )
        await ctx.send(embed=em)

    @lottery.command(name="history")
    async def lottery_history(self, ctx):
        """Show recent lottery draw results."""
        results = await self.bot.db.get_recent_lotteries(5)

        if not results:
            return await ctx.send("No lottery history yet.")

        em = discord.Embed(title="🎰 Lottery History", color=discord.Color.blurple())

        for row in results:
            lottery_id, enrol_price, total_price, winning_number, start_date, end_date = row
            player_count = await self.bot.db.count_lottery_players(lottery_id)
            winners = await self.bot.db.get_lottery_winners(lottery_id, winning_number)

            winner_text = "No winners" if not winners else f"{len(winners)} winner(s)"

            em.add_field(
                name=f"Round #{lottery_id}",
                value=(
                    f"🎯 Number: **{winning_number}** | 💰 Pool: **{total_price:,}** :coin:\n"
                    f"👥 Players: {player_count} | {winner_text}"
                ),
                inline=False
            )

        await ctx.send(embed=em)


async def setup(bot):
    await bot.add_cog(Lottery(bot))

